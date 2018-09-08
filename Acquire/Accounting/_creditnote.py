

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

    def __str__(self):
        if self.is_null():
            return "CreditNote::null"
        else:
            return "CreditNote>>%s" % self.account()

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
        """Return the UID of this credit note. This will match the UID
           of the corresponding debit note
        """
        return self._uid

    @staticmethod
    def from_data(data):
        """Construct and return a new CreditNote from the passed json-decoded
            dictionary
        """
        note = CreditNote()

        if (data and len(data) > 0):
            note._account_uid = data["account_uid"]
            note._uid = data["uid"]
            note._timestamp = data["timestamp"]

        return note

    def to_data(self):
        """Return this credit note as a dictionary that can be
           encoded to json
        """
        data = {}

        if not self.is_null():
            data["account_uid"] = self._account_uid
            data["uid"] = self._uid
            data["timestamp"] = self._timestamp

        return data
