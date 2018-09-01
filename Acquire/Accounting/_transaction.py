
from ._errors import TransactionError

__all__ = ["Transaction"]


class Transaction:
    """This class provides basic information about a transaction - namely
       just the value (always positive) and what the transaction is for
    """
    def __init__(self, value=0, description=None):
        """Create a transaction with the passed value and description. Values
           are positive values with a minimum resolution of 1e-6 (6 decimal
           places) and cannot exceed 999999.999999 (i.e. cannot be 1 million
           or greater). This is to ensure that a value will always fit into a
           f13.6 string (which is used for keys). If you need larger
           transactions, then use the static 'split' function to break
           a single too-large transaction into a list of smaller
           transactions
        """
        value = float(value)

        if value >= Transaction.maximum_transaction_value():
            raise TransactionError(
                "You cannot create a transaction (%s) with a "
                "value greater than %s. Please "
                "use 'split' to break this transaction (%s) into "
                "several separate transactions" %
                (description, Transaction.maximum_transaction_value(), value))

        # ensure that the value is limited in resolution to 6 decimal places
        self._value = float("%13.6f" % value)

        if self._value < 0:
            raise TransactionError(
                "You cannot create a transaction (%s) with a "
                "negative value! %s" % (description, value))

        if description is None:
            if self._value > 0:
                raise TransactionError(
                    "You must give a description to all non-zero "
                    "transactions! %s" % self.value())
            else:
                self._description = None
        else:
            # ensure we are using utf-8 encoded strings
            self._description = str(description).encode("utf-8") \
                                                .decode("utf-8")

    def __str__(self):
        return "%s [%s]" % (self.value(), self.description())

    def is_null(self):
        """Return whether or not this is a null transaction"""
        return self._value == 0 and self._description is None

    def value(self):
        """Return the value of this transaction. This will be always greater
           than or equal to zero
        """
        return self._value

    @staticmethod
    def maximum_transaction_value():
        """Return the maximum value for a single transaction. Currently this
           is 999999.999999 so that a transaction fits into a f013.6 string
        """
        return 999999.999999

    def value_string(self):
        """Return the value of this transaction as a standard-formatted string.
           This will be a string that is formatted as F13.6, with zero padding
           front and back
        """
        return "%013f.6" % self._value

    def description(self):
        """Return the description of this transaction"""
        return self._description

    @staticmethod
    def split(value, description):
        """Split the passed transaction described by 'description' with value
           'value' into a list of transactions that fit the maximum transaction
           limit.
        """
        if value < Transaction.maximum_transaction_value():
            t = Transaction(value, description)
            return [t]
        else:
            values = []

            while value > Transaction.maximum_transaction_value():
                values.append(Transaction.maximum_transaction_value())
                value -= Transaction.maximum_transaction_value()

            transactions = []

            for i in range(0, len(values)):
                transactions.append(Transaction(values[i], "%s: %d of %d" %
                                    (description, i+1, len(values))))

            return transactions

    @staticmethod
    def from_data(data):
        """Return a newly constructed transaction from the passed dictionary
           that has been decoded from json
        """
        transaction = Transaction()

        if (data and len(data) > 0):
            transaction._value = data["value"]
            transaction._description = data["description"]

        return transaction

    def to_data(self):
        """Return this transaction as a dictionary that can be encoded
           to json
        """
        data = {}

        if (data and len(data) > 0):
            data["value"] = self._value
            data["description"] = self._description

        return data
