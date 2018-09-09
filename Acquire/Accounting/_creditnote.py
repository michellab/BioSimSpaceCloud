
from ._debitnote import DebitNote as _DebitNote
from ._decimal import create_decimal as _create_decimal

__all__ = ["CreditNote"]


class CreditNote:
    """This class holds all of the information about a completed credit. This
       is combined with a debit note of equal value to form a transaction
       record
    """
    def __init__(self, debit_note=None, account=None):
        """Create the corresponding credit note for the passed debit_note. This
           will credit value from the note to the passed account. The credit
           will use the same UID as the credit, and the same timestamp. This
           will then be paired with the debit note to form a TransactionRecord
           that can be written to the ledger
        """
        if debit_note is None or account is None:
            self._account_uid = None
            self._timestamp = None
            self._uid = None
            self._debit_note_uid = None
            self._value = _create_decimal(0)
            return

        if not isinstance(debit_note, _DebitNote):
            raise TypeError("You can only create a CreditNote "
                            "with a DebitNote")

        from ._account import Account as _Account

        if not isinstance(account, _Account):
            raise TypeError("You can only creata a CreditNote with an "
                            "Account")

        (uid, timestamp) = account._credit(debit_note)

        self._account_uid = account.uid()
        self._timestamp = timestamp
        self._uid = uid
        self._debit_note_uid = debit_note.uid()
        self._value = debit_note.value()

    def __str__(self):
        if self.is_null():
            return "CreditNote::null"
        else:
            return "CreditNote>>%s" % self.account_uid()

    def is_null(self):
        """Return whether or not this note is null"""
        return self._uid is None

    def account_uid(self):
        """Return the UID of the account to which the value was credited"""
        if self.is_null():
            return None
        else:
            return self._account_uid

    def timestamp(self):
        """Return the timestamp for this credit note"""
        return self._timestamp

    def uid(self):
        """Return the UID of this credit note. This will not match the debit
           note UID - you need to use debit_note_uid() to get the UID of
           the debit note that matches this credit note
        """
        return self._uid

    def debit_note_uid(self):
        """Return the UID of the debit note that matches this credit note.
           While at the moment only a single credit note matches a debit note,
           it may be in the future that we divide a credit over several
           accounts (and thus several credit notes)
        """
        return self._debit_note_uid

    def value(self):
        """Return the value of this note. This may be less than the
           corresponding debit note if only part of the value of the
           debit note is transferred into the account
        """
        return self._value

    @staticmethod
    def from_data(data):
        """Construct and return a new CreditNote from the passed json-decoded
            dictionary
        """
        note = CreditNote()

        if (data and len(data) > 0):
            note._account_uid = data["account_uid"]
            note._uid = data["uid"]
            note._debit_note_uid = data["debit_note_uid"]
            note._timestamp = data["timestamp"]
            note._value = _create_decimal(data["value"])

        return note

    def to_data(self):
        """Return this credit note as a dictionary that can be
           encoded to json
        """
        data = {}

        if not self.is_null():
            data["account_uid"] = self._account_uid
            data["uid"] = self._uid
            data["debit_note_uid"] = self._debit_note_uid
            data["timestamp"] = self._timestamp
            data["value"] = str(self._value)

        return data
