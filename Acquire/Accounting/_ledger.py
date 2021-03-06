
import uuid as _uuid
import datetime as _datetime
from copy import copy as _copy

from Acquire.Service import login_to_service_account \
                    as _login_to_service_account

from Acquire.ObjectStore import ObjectStore as _ObjectStore

from Acquire.Identity import Authorisation as _Authorisation

from ._account import Account as _Account
from ._transaction import Transaction as _Transaction
from ._transactionrecord import TransactionRecord as _TransactionRecord
from ._transactionrecord import TransactionState as _TransactionState
from ._debitnote import DebitNote as _DebitNote
from ._creditnote import CreditNote as _CreditNote
from ._pairednote import PairedNote as _PairedNote
from ._receipt import Receipt as _Receipt
from ._refund import Refund as _Refund

from ._errors import TransactionError, LedgerError, UnbalancedLedgerError

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
    def load_transaction(uid, bucket=None):
        """Load the transactionrecord with UID=uid from the ledger"""
        if bucket is None:
            bucket = _login_to_service_account()

        data = _ObjectStore.get_object_from_json(bucket, Ledger.get_key(uid))

        if data is None:
            raise LedgerError("There is no transaction recorded in the "
                              "ledger with UID=%s (at key %s)" %
                              (uid, Ledger.get_key(uid)))

        return _TransactionRecord.from_data(data)

    @staticmethod
    def save_transaction(record, bucket=None):
        """Save the passed transactionrecord to the object store"""
        if not isinstance(record, _TransactionRecord):
            raise TypeError("You can only write TransactionRecord objects "
                            "to the ledger!")

        if not record.is_null():
            if bucket is None:
                bucket = _login_to_service_account()

            _ObjectStore.set_object_from_json(bucket,
                                              Ledger.get_key(record.uid()),
                                              record.to_data())

    @staticmethod
    def refund(refund, bucket=None):
        """Create and record a new transaction from the passed refund. This
           applies the refund, thereby transferring value from the credit
           account to the debit account of the corresponding transaction.
           Note that you can only refund a transaction once!
           This returns the (already recorded) TransactionRecord for the
           refund
        """
        if not isinstance(refund, _Refund):
            raise TypeError("The Refund must be of type Refund")

        if refund.is_null():
            return _TransactionRecord()

        if bucket is None:
            bucket = _login_to_service_account()

        # return value from the credit to debit accounts
        debit_account = _Account(uid=refund.debit_account_uid(),
                                 bucket=bucket)
        credit_account = _Account(uid=refund.credit_account_uid(),
                                  bucket=bucket)

        # remember that a refund debits from the original credit account...
        # (and can only refund completed (DIRECT) transactions)
        debit_note = _DebitNote(refund=refund, account=credit_account,
                                bucket=bucket)

        # now create the credit note to return the value into the debit account
        try:
            credit_note = _CreditNote(debit_note=debit_note,
                                      refund=refund,
                                      account=debit_account,
                                      bucket=bucket)
        except Exception as e:
            # delete the debit note
            try:
                debit_account._delete_note(debit_note, bucket=bucket)
            except:
                pass

            # reset the transaction to its original state
            try:
                _TransactionRecord.load_test_and_set(
                        refund.transaction_uid(),
                        _TransactionState.REFUNDING,
                        _TransactionState.DIRECT,
                        bucket=bucket)
            except:
                pass

            raise e

        try:
            paired_notes = _PairedNote.create(debit_note, credit_note)
        except Exception as e:
            # delete all records...!
            try:
                debit_account._delete_note(debit_note, bucket=bucket)
            except:
                pass

            try:
                credit_account._delete_note(credit_note, bucket=bucket)
            except:
                pass

            # reset the transaction to the pending state
            try:
                _TransactionRecord.load_test_and_set(
                        refund.transaction_uid(),
                        _TransactionState.REFUNDING,
                        _TransactionState.DIRECT,
                        bucket=bucket)
            except:
                pass

            raise e

        # now record the two entries to the ledger. The below function
        # is guaranteed not to raise an exception
        return Ledger._record_to_ledger(paired_notes, refund=refund,
                                        bucket=bucket)

    @staticmethod
    def receipt(receipt, bucket=None):
        """Create and record a new transaction from the passed receipt. This
           applies the receipt, thereby actually transferring value from the
           debit account to the credit account of the corresponding
           transaction. Note that you can only receipt a transaction once!
           This returns the (already recorded) TransactionRecord for the
           receipt
        """
        if not isinstance(receipt, _Receipt):
            raise TypeError("The Receipt must be of type Receipt")

        if receipt.is_null():
            return _TransactionRecord()

        if bucket is None:
            bucket = _login_to_service_account()

        # extract value into the debit note
        debit_account = _Account(uid=receipt.debit_account_uid(),
                                 bucket=bucket)
        credit_account = _Account(uid=receipt.credit_account_uid(),
                                  bucket=bucket)

        debit_note = _DebitNote(receipt=receipt, account=debit_account,
                                bucket=bucket)

        # now create the credit note to put the value into the credit account
        try:
            credit_note = _CreditNote(debit_note=debit_note,
                                      receipt=receipt,
                                      account=credit_account,
                                      bucket=bucket)
        except Exception as e:
            # delete the debit note
            try:
                debit_account._delete_note(debit_note, bucket=bucket)
            except:
                pass

            # reset the transaction to the pending state
            try:
                _TransactionRecord.load_test_and_set(
                        receipt.transaction_uid(),
                        _TransactionState.RECEIPTING,
                        _TransactionState.PENDING,
                        bucket=bucket)
            except:
                pass

            raise e

        try:
            paired_notes = _PairedNote.create(debit_note, credit_note)
        except Exception as e:
            # delete all records...!
            try:
                debit_account._delete_note(debit_note, bucket=bucket)
            except:
                pass

            try:
                credit_account._delete_note(credit_note, bucket=bucket)
            except:
                pass

            # reset the transaction to the pending state
            try:
                _TransactionRecord.load_test_and_set(
                        receipt.transaction_uid(),
                        _TransactionState.RECEIPTING,
                        _TransactionState.PENDING,
                        bucket=bucket)
            except:
                pass

            raise e

        # now record the two entries to the ledger. The below function
        # is guaranteed not to raise an exception
        return Ledger._record_to_ledger(paired_notes, receipt=receipt,
                                        bucket=bucket)

    @staticmethod
    def perform(transactions, debit_account, credit_account, authorisation,
                is_provisional=False, bucket=None):
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

        if is_provisional:
            is_provisional = True
        else:
            is_provisional = False

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

        if bucket is None:
            bucket = _login_to_service_account()

        # first, try to debit all of the transactions. If any fail (e.g.
        # because there is insufficient balance) then they are all
        # immediately refunded
        debit_notes = []
        try:
            for transaction in transactions:
                debit_notes.append(_DebitNote(transaction, debit_account,
                                              authorisation, is_provisional,
                                              bucket=bucket))
        except Exception as e:
            # refund all of the completed debits
            credit_notes = []
            debit_error = str(e)
            try:
                for debit_note in debit_notes:
                    debit_account._delete_note(debit_note, bucket=bucket)
            except Exception as e:
                raise UnbalancedLedgerError(
                    "We have an unbalanced ledger as it was not "
                    "possible to refund a multi-part refused credit (%s): "
                    "Credit refusal error = %s. Refund error = %s" %
                    (str(debit_note), str(debit_error), str(e)))

            # raise the original error to show that, e.g. there was
            # insufficient balance
            raise e

        # now create the credit note(s) for this transaction. This will credit
        # the account, thereby transferring value from the debit_note(s) to
        # that account. If this fails then the debit_note(s) needs to
        # be refunded
        credit_notes = {}
        has_error = False
        credit_error = Exception()
        for debit_note in debit_notes:
            try:
                credit_note = _CreditNote(debit_note, credit_account,
                                          bucket=bucket)
                credit_notes[debit_note.uid()] = credit_note
            except Exception as e:
                has_error = True
                credit_error = e
                break

        if has_error:
            # something went wrong crediting the account... We need to refund
            # the transaction - first retract the credit notes...
            try:
                for credit_note in credit_notes.values():
                    credit_account._delete_note(credit_note, bucket=bucket)
            except Exception as e:
                raise UnbalancedLedgerError(
                    "We have an unbalanced ledger as it was not "
                    "possible to credit a multi-part debit (%s): Credit "
                    "refusal error = %s. Refund error = %s" %
                    (debit_notes, str(credit_error), str(e)))

            # now refund all of the debit notes
            try:
                for debit_note in debit_notes:
                    debit_account._delete_note(debit_note, bucket=bucket)
            except Exception as e:
                raise UnbalancedLedgerError(
                    "We have an unbalanced ledger as it was not "
                    "possible to credit a multi-part debit (%s): Credit "
                    "refusal error = %s. Refund error = %s" %
                    (debit_notes, str(credit_error), str(e)))

            raise credit_error

        try:
            paired_notes = _PairedNote.create(debit_notes, credit_notes)
        except Exception as e:
            # delete all of the notes...
            for debit_note in debit_notes:
                try:
                    debit_account._delete_note(debit_note, bucket=bucket)
                except:
                    pass

            for credit_note in credit_notes:
                try:
                    credit_account._delete_note(credit_note, bucket=bucket)
                except:
                    pass

            raise e

        # now write the paired entries to the ledger. The below function
        # is guaranteed not to raise an exception
        return Ledger._record_to_ledger(paired_notes, is_provisional,
                                        bucket=bucket)

    @staticmethod
    def _record_to_ledger(paired_notes, is_provisional=False,
                          receipt=None, refund=None, bucket=None):
        """Internal function used to generate and record transaction records
           from the passed paired debit- and credit-note(s). This will write
           the transaction record(s) to the object store, and will also return
           the record(s).
        """
        if receipt is not None:
            if not isinstance(receipt, _Receipt):
                raise TypeError("Receipts must be of type 'Receipt'")

        if refund is not None:
            if not isinstance(refund, _Refund):
                raise TypeError("Refunds must be of type 'Refund'")

        try:
            records = []

            if bucket is None:
                bucket = _login_to_service_account()

            for paired_note in paired_notes:
                record = _TransactionRecord()
                record._debit_note = paired_note.debit_note()
                record._credit_note = paired_note.credit_note()

                if is_provisional:
                    record._transaction_state = _TransactionState.PROVISIONAL
                else:
                    record._transaction_state = _TransactionState.DIRECT

                if receipt is not None:
                    record._receipt = receipt

                if refund is not None:
                    record._refund = refund

                Ledger.save_transaction(record, bucket)

                records.append(record)

            if len(records) == 1:
                return records[0]
            else:
                return records

        except:
            # an error occuring here will break the system, which will
            # require manual cleaning. Mark this as broken!
            try:
                Ledger._set_truly_broken(paired_notes, bucket)
            except:
                pass

            raise SystemError("The ledger is in a very broken state!")

    @staticmethod
    def _set_truly_broken(paired_notes, bucket):
        """Internal function called when an irrecoverable error state
           is detected. This records the notes that caused the error and
           places the affected accounts into an error state
        """
        raise NotImplementedError("_set_truly_broken needs to be implemented!")
