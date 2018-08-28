
import uuid as _uuid
import datetime as _datetime
from copy import copy as _copy

from Acquire.Service import login_to_service_account as _login_to_service_account
from Acquire.ObjectStore import ObjectStore as _ObjectStore

from ._errors import TransactionError

__all__ = [ "Transaction", "TransactionRecord" ]

def _transaction_root():
    return "transactions"

class Transaction:
    """This class provides basic information about a transaction - namely
       just the value (always positive) and what the transaction is for
    """
    def __init__(self, value=0, description=None):
        """Create a transaction with the passed value and description"""
        self._value = float(value)

        if self._value < 0:
            raise TransactionError("You cannot create a transaction (%s) with a "
                                   "negative value! %2" % (description,value))

        if self._description is None and self._value > 0:
            raise TransactionError("You must give a description to all non-zero transactions! %s" % \
                                    self.value())

        self._description = str(description).encode("utf-8").decode("utf-8")

    def __str__(self):
        return "%s [%s]" % (self.value(),self.description())

    def value(self):
        """Return the value of this transaction. This will be always greater
           than or equal to zero
        """
        return self._value

    def description(self):
        """Return the description of this transaction"""
        return self._description

    @staticmethod
    def from_data(data):
        """Return a newly constructed transaction from the passed dictionary
           that has been decoded from json
        """
        transaction = Transaction()

        transaction._value = data["value"]
        transaction._description = data["description"]

        return transaction

    def to_data(self):
        """Return this transaction as a dictionary that can be encoded to json"""
        data = {}
        data["value"] = self._value
        data["description"] = self._description
        return data

class TransactionRecord:
    """This class holds a record of a transaction that has already been written to 
       the accounting ledger. This records a unique ID, the timestamp of the entry, 
       the value, the two accounts involved in the transaction (debit account to credit account),
       a description of what the transaction refers to, 
       and who/how the transaction was authorised. If 'is_provisional'
       then this is a provisional transaction that is recorded as a liability
       for the debtor and a future income for the creditor. This is confirmed
       by creating a receipt via "receipt_for" by passing the UID for the
       transaction this receipts, and the actual 'value' of the receipt.
       Note that the actual value CANNOT exceed the original provisional value
       that was agreed by the debtor
    """
    def __init__(self, uid=None):
        """Load the transaction record from the object store using the passed UID"""

        if uid:
            self._load_transaction(uid)
        else:
            self._transaction = None
            self._debit_record = None
            self._credit_record = None
            self._is_receipted = False

    def __str__(self):
        """Return a string representation of this transaction"""
        if self._uid is None or self._credit_account is None:
            return "%s | unapplied" % str(self.transaction())

        elif self._is_receipted:
            return "%s [%s] from %s to %s | receipted" % \
                        (str(self.transaction()), self.debit_account(), self.credit_account())

        else:
            return "%s [%s] from %s to %s | PROVISIONAL" % \
                        (str(self.transaction()), self.debit_account(), self.credit_account())

    def uid(self):
        """Return the UID for this transaction record"""
        return self._uid

    def transaction(self):
        """Return the transaction underlying this record"""
        return self._transaction

    def credit_account(self):
        return self._credit_record.credit_account()

    def debit_account(self):
        return self._debit_record.debit_account()

    def key(self, uid=None):
        """Return the key for this transaction in the object store"""
        if uid is None:
            uid = self._uid

        return "%s/%s" % (_transaction_root(), uid)

    def timestamp(self):
        """Return the timestamp when this transaction was applied"""
        return self._timestamp

    def is_applied(self):
        """Return whether or not this transaction has already been applied"""
        return not (self._debit_account is None)

    def is_receipted(self):
        """Return whether or not this transaction has been receipted"""
        return self._is_receipted

    def is_provisional(self):
        """Return whether or not this transaction is provisional"""
        return not (self.is_applied() or self.is_receipted())

    @staticmethod
    def receipt(receipt):
        """Create and record a new transaction from the passed receipt. This
           applies the receipt, thereby actually transferring value from the
           debit account to the credit account of the corresponding transaction.
           Not that you can only receipt a transaction once! This returns the
           actual transaction object created for the receipt, which will already
           have been applied and written to the object store
        """
        transaction = TransactionRecord( uid=receipt.transaction_uid() )

        if transaction.is_receipted():
            raise TransactionError("It is an error to try to receipt a transaction twice! %s | %s" % \
                            (str(transaction), str(receipt)))

        return TransactionRecord()

    @staticmethod
    def perform(transaction, debit_account, credit_account, authorisation, is_provisional=False):
        """Perform the passed transaction between 'debit_account' and 'credit_account', recording
           the 'authorisation' for this transaction. If 'is_provisional' then record this
           as a provisional transaction (liability for the debit_account, future unspendable
           income for the 'credit_account'). Payment won't actually be taken until the
           transaction is 'receipted' (which may be for less than (but not more than) then
           provisional value. Returns the (already recorded) TransactionRecord
        """

        if transaction.value() <= 0:
            # no point recording zero transactions
            return TransactionRecord()

        # try to debit the account using this record
        debit_record = debit_account.debit(transaction, authorisation, is_provisional)
        debit_record.assert_succeeded()

        credit_record = credit_account.credit(transaction, debit_record)

        if not credit_record.succeeded():
            # reverse the debit...
            debit_account.reverse_debit(debit_record)

            raise TransactionError("Failed to complete the transaction...")

        #save everything to the object store immediately
        record = TransactionRecord()
        record._transaction = transaction
        record._debit_record = debit_record
        record._credit_record = credit_record
        record._is_receipted = not is_provisional

        record._save_transaction()
        return record

    def _load_transaction(self, uid):
        """Load this transaction from the object store"""
        bucket = _login_to_service_account()
        data = _ObjectStore.get_object_from_json(bucket, self.key(uid))
        self.__dict__ = _copy( Transaction.from_data(data) )

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
            record._transaction = Transaction.from_data(data["transaction"])
            record._credit_record = CreditRecord.from_data(data["credit_record"])
            record._debit_record = DebitRecord.from_data(data["debit_record"])
            record._is_receipted = data["is_receipted"]

        return record

    def to_data(self):
        """Return this transaction as a dictionary that can be encoded to json"""
        data = {}

        if not self._transaction is None:
            data["transaction"] = self._transaction.to_data()
            data["credit_record"] = self._credit_record.to_data()
            data["debit_record"] = self._debit_record.to_data()
            data["is_receipted"] = self._is_receipted

        return data
