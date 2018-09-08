
import uuid as _uuid
import datetime as _datetime
from copy import copy as _copy

from Acquire.Service import login_to_service_account \
                    as _login_to_service_account

from Acquire.ObjectStore import ObjectStore as _ObjectStore

from ._account import Account as _Account
from ._transaction import Transaction as _Transaction
from ._debitnote import DebitNote as _DebitNote
from ._creditnote import CreditNote as _CreditNote
from ._pairednote import PairedNote as _PairedNote
from ._receipt import Receipt as _Receipt

from ._errors import TransactionError, UnbalancedLedgerError

__all__ = ["TransactionRecord"]


def _transaction_root():
    return "transactions"


class TransactionRecord:
    """This class holds a record of a transaction that has already been
       written to the accounting ledger. This records a unique ID, the
       timestamp of the entry, the value, the two accounts involved in the
       transaction (debit account to credit account), a description of what
       the transaction refers to, and who/how the transaction was authorised.
       If 'is_provisional' then this is a provisional transaction that is
       recorded as a liability for the debtor and a future income for the
       creditor. This is confirmed by creating a receipt via "receipt_for"
       by passing the UID for the transaction this receipts, and the actual
       'value' of the receipt. Note that the actual value CANNOT exceed the
       original provisional value that was agreed by the debtor
    """
    def __init__(self, uid=None):
        """Load the transaction record from the object store using the
           passed UID
        """
        if uid:
            self._load_transaction(uid)
        else:
            self._debit_note = None
            self._credit_note = None
            self._is_receipted = False

    def __str__(self):
        """Return a string representation of this transaction"""
        if self.is_null():
            return "TransactionRecord::null"

        s = "%s : %s transferred from %s to %s" % \
            (self.description(),
             self.value(), self.debit_note().account(),
             self.credit_note().account())

        if self._is_receipted:
            return "%s | receipted" % s
        else:
            return "%s | PROVISIONAL" % s

    def is_null(self):
        """Return whether or not this is a null record"""
        return self._debit_note is None

    def description(self):
        """Return the description of this transaction"""
        if self.is_null():
            return None
        else:
            return self.transaction().description()

    def value(self):
        """Return the value of this transaction"""
        if self.is_null():
            return 0
        else:
            return self.transaction().value()

    def uid(self):
        """Return the UID for this transaction record"""
        if self.is_null():
            return None
        else:
            return self.debit_note().uid()

    def transaction(self):
        """Return the transaction underlying this record"""
        if self.is_null():
            return None
        else:
            return self.debit_note().transaction()

    def credit_account(self):
        """Return the UID of the account to which value has been credited"""
        if self.is_null():
            return None
        else:
            return self.credit_note().account()

    def credit_note(self):
        """Return the credit note for this transaction. This is the note
           recording that value has been credited to an account. A
           TransactionRecord is the pairing of a DebitNote with a CreditNote
        """
        return self._credit_note

    def debit_note(self):
        """Return the debit note for this transaction. This is the note
           recording that value has been debited to an account. A
           TransactionRecord is the pairing of a DebitNote with a CreditNote
        """
        return self._debit_note

    def debit_account(self):
        """Return the UID of the account from which value has been debited"""
        if self.is_null():
            return None
        else:
            return self.debit_note().account()

    def key(self, uid=None):
        """Return the key for this transaction in the object store"""
        if self.is_null():
            return None
        else:
            return "%s/%s" % (_transaction_root(), self.debit_note().uid())

    def timestamp(self):
        """Return the timestamp when this transaction was applied"""
        if self.is_null():
            return None
        else:
            return self.debit_note().timestamp()

    def is_receipted(self):
        """Return whether or not this transaction has been receipted"""
        if self.is_null():
            return False
        else:
            return self._is_receipted

    def is_provisional(self):
        """Return whether or not this transaction is provisional"""
        return not (self.is_null() or self.is_receipted())

    def is_refund(self):
        """Return whether or not this transaction is a refund"""
        return not (self._refund_reason is None)

    def refund_reason(self):
        """Return the reason for the refund"""
        return self._refund_reason

    @staticmethod
    def receipt(receipt):
        """Create and record a new transaction from the passed receipt. This
           applies the receipt, thereby actually transferring value from the
           debit account to the credit account of the corresponding
           transaction. Not that you can only receipt a transaction once!
           This returns the actual transaction object created for the receipt,
           which will already have been applied and written to the object store
        """
        transaction = TransactionRecord(uid=receipt.transaction_uid())

        if transaction.is_receipted():
            raise TransactionError(
                "It is an error to try to receipt a transaction twice! %s | %s"
                % (str(transaction), str(receipt)))

        return transaction

    @staticmethod
    def perform(transactions, debit_account, credit_account, authorisation,
                is_provisional=False):
        """Perform the passed transaction(s) between 'debit_account' and
           'credit_account', recording the 'authorisation' for this
           transaction. If 'is_provisional' then record this as a provisional
           transaction (liability for the debit_account, future unspendable
           income for the 'credit_account'). Payment won't actually be taken
           until the transaction is 'receipted' (which may be for less than
           (but not more than) then provisional value. Returns the (already
           recorded) TransactionRecord.

           Note that if several transactions are passed, then they must all
           succeed. If one of them fails then they are immediately refunded.
        """

        try:
            transactions[0]
        except:
            transactions = [transactions]

        # remove any zero transactions, as they are not worth recording
        t = []
        for transaction in transactions:
            if transaction.value() >= 0:
                t.append(transaction)

        transactions = t

        # first, try to debit all of the transactions. If any fail (e.g.
        # because there is insufficient balance) then they are all
        # immediately refunded
        debit_notes = []
        try:
            for transaction in transactions:
                debit_notes.append(_DebitNote(transaction, debit_account,
                                              authorisation, is_provisional))
        except Exception as e:
            # refund all of the completed debits
            credit_notes = []
            debit_error = str(e)
            try:
                for debit_note in debit_notes:
                    credit_notes.append(_CreditNote(debit_note, debit_account))
            except Exception as e:
                raise UnbalancedLedgerError(
                    "We have an unbalanced ledger as it was not "
                    "possible to refund a multi-part refused credit (%s): "
                    "Credit refusal error = %s. Refund error = %s" %
                    (str(debit_note), str(debit_error), str(e)))

            if len(debit_notes) > 0:
                # record all of this to the ledger
                TransactionRecord._record_to_ledger(
                    debit_notes, credit_notes,
                    is_provisional, debit_error)

            # raise the original error to show that, e.g. there was
            # insufficient balance
            raise e

        # now create the credit note(s) for this transaction. This will credit
        # the account, thereby transferring value from the debit_note(s) to
        # that account. If this fails then the debit_note(s) needs to
        # be refunded
        credit_notes = {}
        credit_error = None
        for debit_note in debit_notes:
            try:
                credit_note = _CreditNote(debit_note, credit_account)
                credit_notes[debit_note.uid()] = credit_note
            except Exception as e:
                credit_error = str(e)
                raise e

        if len(credit_notes) != len(debit_notes):
            # something went wrong crediting the account... We need to refund
            # the transaction - first retract the credit notes...
            try:
                for credit_note in credit_notes.values():
                    # NEED TO WRITE THIS CODE
                    # credit_account.cancel_transaction(credit_note)
                    pass
            except:
                pass

            # now refund all of the debit notes
            credit_notes = {}
            try:
                for debit_note in debit_notes:
                    credit_notes[debit_note.uid()] = _CreditNote(debit_note,
                                                                 debit_account)
            except Exception as e:
                raise UnbalancedLedgerError(
                    "We have an unbalanced ledger as it was not "
                    "possible to credit a multi-part debit (%s): Credit "
                    "refusal error = %s. Refund error = %s" %
                    (debit_notes, str(credit_error), str(e)))


        return TransactionRecord._record_to_ledger(
                    _PairedNote.create(debit_notes, credit_notes),
                    is_provisional, credit_error)

    @staticmethod
    def _record_to_ledger(debit_notes, credit_notes, is_provisional,
                          refund_reason=None):
        """Internal function used to generate and record transaction records
           from the passed paired debit- and credit-note(s). This will write
           the transaction record(s) to the object store, and will also return
           the record(s). If 'refund_reason' is passed, then this is a failed
           transaction that is actually a refund. Refund transactions are
           always immediately receipted if they are provisional.
        """
        try:
            debit_notes[0]
        except:
            debit_notes = [debit_notes]

        try:
            credit_notes[0]
        except:
            credit_notes = [credit_notes]

        if len(debit_notes) != len(credit_notes):
            raise TransactionError(
                "You must have a matching number of debit notes (%s) "
                "as you have credit notes (%s)" %
                (len(debit_notes), len(credit_notes)))

        records = []

        for i in range(0, len(debit_notes)):
            record = TransactionRecord()
            record._debit_note = debit_notes[i]
            record._credit_note = credit_notes[i]
            record._is_receipted = not is_provisional

            if refund_reason:
                record._refund_reason = str(refund_reason)
            else:
                record._refund_reason = None

            record._save_transaction()

            if is_provisional and refund_reason:
                records.append(TransactionRecord.receipt(
                               _Receipt(record.uid())))
            else:
                records.append(record)

        if len(records) == 1:
            return records[0]
        else:
            return records

    def _load_transaction(self, uid):
        """Load this transaction from the object store"""
        bucket = _login_to_service_account()
        data = _ObjectStore.get_object_from_json(bucket, self.key(uid))
        self.__dict__ = _copy(TransactionRecord.from_data(data))

    def _save_transaction(self):
        """Save this transaction to the object store"""
        bucket = _login_to_service_account()
        _ObjectStore.set_object_from_json(bucket, self.key(), self.to_data())

    @staticmethod
    def from_data(data):
        """Construct and return a new Transaction from the passed json-decoded
            dictionary
        """
        record = TransactionRecord()

        if (data and len(data) > 0):
            record._credit_note = _CreditNote.from_data(data["credit_note"])
            record._debit_note = _DebitNote.from_data(data["debit_note"])
            record._is_receipted = data["is_receipted"]

            if "refund_reason" in data:
                record._refund_reason = data["refund_reason"]

        return record

    def to_data(self):
        """Return this transaction as a dictionary that can be
           encoded to json
        """
        data = {}

        if not self.is_null():
            data["credit_note"] = self._credit_note.to_data()
            data["debit_note"] = self._debit_note.to_data()
            data["is_receipted"] = self._is_receipted

            if not (self._refund_reason is None):
                data["refund_reason"] = self._refund_reason

        return data
