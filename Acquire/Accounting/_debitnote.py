

from ._transaction import Transaction as _Transaction
from ._authorisation import Authorisation as _Authorisation

__all__ = ["DebitNote"]


class DebitNote:
    """This class holds all of the information about a completed debit. This
       is combined with credit note of equal value to form a transaction record
    """
    def __init__(self, transaction=None, account=None, authorisation=None,
                 is_provisional=False, bucket=None):
        """Create a debit note for the passed transaction will debit value
           from the passed account. The note will create a unique ID (uid)
           for the debit, plus the timestamp of the time that value was drawn
           from the debited account. This debit note will be paired with a
           corresponding credit note from the account that received the value
           from the transaction so that a balanced TransactionRecord can be
           written to the ledger
        """
        if transaction is None or account is None:
            self._transaction = None
            return

        if not isinstance(transaction, _Transaction):
            raise TypeError("You can only create a DebitNote with a "
                            "Transaction")

        from ._account import Account as _Account

        if not isinstance(account, _Account):
            raise TypeError("You can only create a DebitNote with a valid "
                            "Account")

        if authorisation is not None:
            from ._authorisation import Authorisation as _Authorisation

            if not isinstance(authorisation, _Authorisation):
                raise TypeError("Authorisation must be of type Authorisation")

        self._transaction = transaction
        self._account_uid = account.uid()
        self._authorisation = authorisation
        self._is_provisional = is_provisional

        (uid, timestamp) = account._debit(transaction, authorisation,
                                          is_provisional, bucket=bucket)

        self._timestamp = float(timestamp)
        self._uid = str(uid)

    def __str__(self):
        if self.is_null():
            return "DebitNote::null"
        else:
            return "DebitNote<<%s [%s]" % (self.account_uid(), self.value())

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._uid == other._uid
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def is_null(self):
        """Return whether or not this is a null note"""
        return self._transaction is None

    def uid(self):
        """Return the UID for this note. This has the format
           dd:mm:yyyy/unique_string
        """
        if self.is_null():
            return None
        else:
            return self._uid

    def timestamp(self):
        """Return the timestamp for when value was debited from the account"""
        if self.is_null():
            return None
        else:
            return self._timestamp

    def account_uid(self):
        """Return the UID of the account that was debited"""
        if self.is_null():
            return None
        else:
            return self._account_uid

    def transaction(self):
        """Return the transaction related to this debit note"""
        if self.is_null():
            return None
        else:
            return self._transaction

    def value(self):
        """Return the value of this note"""
        if self.is_null():
            return 0
        else:
            return self.transaction().value()

    def authorisation(self):
        """Return the authorisation that was used successfully to withdraw
           value from the debited account
        """
        if self.is_null():
            return None
        else:
            return self._authorisation

    def is_provisional(self):
        """Return whether or not the debit was provisional. Provisional debits
           are listed as liabilities
        """
        if self.is_null():
            return False
        else:
            return self._is_provisional

    def to_data(self):
        """Return this DebitNote as a dictionary that can be encoded as json"""
        data = {}

        if not self.is_null():
            data["transaction"] = self._transaction.to_data()
            data["account_uid"] = self._account_uid
            data["authorisation"] = self._authorisation.to_data()
            data["is_provisional"] = self._is_provisional
            data["timestamp"] = self._timestamp
            data["uid"] = self._uid

        return data

    @staticmethod
    def from_data(data):
        """Return a DebitNote that has been extracted from the passed
           json-decoded dictionary
        """
        d = DebitNote()

        if (data and len(data) > 0):
            d._transaction = data["transaction"]
            d._account_uid = data["account_uid"]
            d._authorisation = _Authorisation.from_data(data["authorisation"])
            d._is_provisional = data["is_provisional"]
            d._timestamp = data["timestamp"]
            d._uid = data["uid"]

        return d
