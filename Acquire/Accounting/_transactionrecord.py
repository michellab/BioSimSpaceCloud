
import uuid as _uuid
import datetime as _datetime
from copy import copy as _copy

from Acquire.Service import login_to_service_account \
                    as _login_to_service_account

from Acquire.ObjectStore import ObjectStore as _ObjectStore

from ._account import Account as _Account
from ._authorisation import Authorisation as _Authorisation
from ._transaction import Transaction as _Transaction
from ._debitnote import DebitNote as _DebitNote
from ._creditnote import CreditNote as _CreditNote
from ._pairednote import PairedNote as _PairedNote
from ._receipt import Receipt as _Receipt

from ._errors import TransactionError, UnbalancedLedgerError

__all__ = ["TransactionRecord"]


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
            self._is_refunded = False
            self._refund_reason = None
            self._receipt = None

    def __str__(self):
        """Return a string representation of this transaction"""
        if self.is_null():
            return "TransactionRecord::null"

        s = "%s : %s transferred from %s to %s" % \
            (self.description(),
             self.value(), self.debit_note().account_uid(),
             self.credit_note().account_uid())

        if self._is_receipted:
            return "%s | receipted" % s
        elif self._is_refunded:
            return "%s | REFUNDED" % s
        else:
            return "%s | PROVISIONAL" % s

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._debit_note == other._debit_note and \
                   self._credit_note == other._credit_note and \
                   self._is_receipted == other._is_receipted and \
                   self._is_refunded == other._is_refunded
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

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

    def credit_account_uid(self):
        """Return the UID of the account to which value has been credited"""
        if self.is_null():
            return None
        else:
            return self.credit_note().account_uid()

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

    def debit_account_uid(self):
        """Return the UID of the account from which value has been debited"""
        if self.is_null():
            return None
        else:
            return self.debit_note().account_uid()

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

    def is_refunded(self):
        """Return whether or not this transaction has been refunded"""
        if self.is_null():
            return False
        else:
            return self._is_refunded

    def is_provisional(self):
        """Return whether or not this transaction is provisional"""
        return not (self.is_null() or self.is_receipted())

    def is_refund(self):
        """Return whether or not this transaction is a refund"""
        return self._refund_reason is not None

    def is_receipt(self):
        """Return whether or not this transaction is a receipt"""
        return self._receipt is not None

    def refund_reason(self):
        """Return the reason for the refund"""
        return self._refund_reason

    def receipt(self):
        """Return the receipt underlying this transaction"""
        return self._receipt

    def _load_transaction(self, uid):
        """Load this transaction from the object store"""
        from ._ledger import Ledger as _Ledger
        self.__dict__ = _copy(_Ledger.load_transaction(uid))

    def _save_transaction(self):
        """Save this transaction to the object store"""
        from ._ledger import Ledger as _Ledger
        _Ledger.save_transaction(self)

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
            record._is_refunded = data["is_refunded"]

            if "refund_reason" in data:
                record._refund_reason = data["refund_reason"]
            else:
                record._refund_reason = None

            if "receipt" in data:
                record._receipt = _Receipt.from_data(data["receipt"])
            else:
                record._receipt = None

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
            data["is_refunded"] = self._is_refunded

            if self._refund_reason is not None:
                data["refund_reason"] = self._refund_reason

            if self._receipt is not None:
                data["receipt"] = self._receipt.to_data()

        return data
