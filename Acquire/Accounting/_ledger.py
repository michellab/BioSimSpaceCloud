
import uuid as _uuid
import datetime as _datetime
from copy import copy as _copy

from Acquire.Service import login_to_service_account \
                    as _login_to_service_account

from Acquire.ObjectStore import ObjectStore as _ObjectStore

from ._account import Account as _Account
from ._authorisation import Authorisation as _Authorisation
from ._transaction import Transaction as _Transaction
from ._transactionrecord import TransactionRecord as _TransactionRecord
from ._debitnote import DebitNote as _DebitNote
from ._creditnote import CreditNote as _CreditNote
from ._pairednote import PairedNote as _PairedNote
from ._receipt import Receipt as _Receipt

from ._errors import TransactionError, UnbalancedLedgerError

__all__ = ["Ledger"]


class Ledger:
    """This is a static class which manages the global ledger for the
       entire accounting service
    """
    @staticmethod
    def get_key(uid):
        """Return the object store key for the transactionrecord with
           UID=uid
        """
        return "transactions/%s" % (str(uid))

    @staticmethod
    def load_transaction(uid):
        """Load the transactionrecord with UID=uid from the ledger"""
        bucket = _login_to_service_account()
        data = _ObjectStore.get_object_from_json(bucket, Ledger.get_key(uid))
        return _TransactionRecord.from_data(data)

    @staticmethod
    def save_transaction(record):
        """Save the passed transactionrecord to the object store"""
        if not isinstance(record, _TransactionRecord):
            raise TypeError("You can only write TransactionRecord objects "
                            "to the ledger!")

        if not record.is_null():
            bucket = _login_to_service_account()
            _ObjectStore.set_object_from_json(bucket,
                                              Ledger.get_key(record.uid()),
                                              record.to_data())

    @staticmethod
    def refund(refund, authorisation):
        """Create and record a new transaction from the passed refund. This
           applies the refund, thereby transferring value from the credit
           account to the debit account of the corresponding transaction.
           Note that you can only refund a transaction once!
           This returns the (already recorded) TransactionRecord for the
           refund
        """
        raise NotImplementedError("Have not implmented refunding a "
                                  "transaction")

    @staticmethod
    def receipt(receipt, authorisation):
        """Create and record a new transaction from the passed receipt. This
           applies the receipt, thereby actually transferring value from the
           debit account to the credit account of the corresponding
           transaction. Note that you can only receipt a transaction once!
           This returns the (already recorded) TransactionRecord for the
           receipt
        """
        if not isinstance(receipt, _Receipt):
            raise TypeError("The Receipt must be of type Receipt")

        if not isinstance(authorisation, _Authorisation):
            raise TypeError("The Authorisation must be of type Authorisation")

        if receipt.is_null():
            return

        # get the debit and credit ac

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

        if not isinstance(debit_account, _Account):
            raise TypeError("The Debit Account must be of type Account")

        if not isinstance(credit_account, _Account):
            raise TypeError("The Credit Account must be of type Account")

        if not isinstance(authorisation, _Authorisation):
            raise TypeError("The Authorisation must be of type Authorisation")

        try:
            transactions[0]
        except:
            transactions = [transactions]

        # remove any zero transactions, as they are not worth recording
        t = []
        for transaction in transactions:
            if not isinstance(transaction, _Transaction):
                raise TypeError("The Transaction must be of type Transaction")

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
                Ledger._record_to_ledger(
                    _PairedNote.create(debit_notes, credit_notes),
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

        return Ledger._record_to_ledger(
                _PairedNote.create(debit_notes, credit_notes),
                is_provisional, credit_error)

    @staticmethod
    def _record_to_ledger(paired_notes, is_provisional,
                          refund_reason=None):
        """Internal function used to generate and record transaction records
           from the passed paired debit- and credit-note(s). This will write
           the transaction record(s) to the object store, and will also return
           the record(s). If 'refund_reason' is passed, then this is a failed
           transaction that is actually a refund. Refund transactions are
           always immediately receipted if they are provisional.
        """
        records = []

        for paired_note in paired_notes:
            record = _TransactionRecord()
            record._debit_note = paired_note.debit_note()
            record._credit_note = paired_note.credit_note()
            record._is_receipted = not is_provisional

            if refund_reason:
                record._refund_reason = str(refund_reason)
            else:
                record._refund_reason = None

            Ledger.save_transaction(record)

            if is_provisional and refund_reason:
                records.append(Ledger.receipt(
                               _Receipt(record.uid()), _Authorisation()))
            else:
                records.append(record)

        if len(records) == 1:
            return records[0]
        else:
            return records
