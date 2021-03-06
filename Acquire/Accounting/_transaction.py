
from decimal import Decimal as _Decimal
from decimal import Context as _Context

from ._errors import TransactionError

__all__ = ["Transaction"]


def _getcontext():
    """Return the context used for all decimals in transactions. This
       context rounds to 6 decimal places and provides sufficient precision
       to support any value between 0 and 999,999,999,999,999.999,999,999
       (i.e. everything up to just under one quadrillion - I doubt we will
        ever have an account that has more than a trillion units in it!)
    """
    return _Context(prec=24)


def _create_decimal(value):
    """Create a decimal from the passed value. This is a decimal that
       has 6 decimal places and is clamped between 0 <= value < 1 quadrillion
    """
    try:
        d = _Decimal("%.6f" % value, _getcontext())
    except:
        value = _Decimal(value, _getcontext())
        d = _Decimal("%.6f" % value, _getcontext())

    if d < 0:
        raise TransactionError(
                "You cannot create a transaction with a negative value (%s)"
                % (value))

    elif d >= 1000000000000000:
        raise TransactionError(
                "You cannot create a transaction with a value greater than "
                "1 quadrillion! (%s)" % (value))

    return d


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
        value = _create_decimal(value)

        if value > Transaction.maximum_transaction_value():
            raise TransactionError(
                "You cannot create a transaction (%s) with a "
                "value greater than %s. Please "
                "use 'split' to break this transaction (%s) into "
                "several separate transactions" %
                (description, Transaction.maximum_transaction_value(), value))

        # ensure that the value is limited in resolution to 6 decimal places
        self._value = value

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

    def __eq__(self, other):
        if isinstance(other, Transaction):
            return self.value() == other.value() and \
                   self.description() == other.description()
        else:
            return self.value() == _create_decimal(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        if isinstance(other, Transaction):
            return self.value() < other.value()
        else:
            return self.value() < _create_decimal(other)

    def __gt__(self, other):
        if isinstance(other, Transaction):
            return self.value() > other.value()
        else:
            return self.value() > _create_decimal(other)

    def __ge__(self, other):
        return self.__eq__(other) or self.__gt__(other)

    def __le__(self, other):
        return self.__eq__(other) or self.__lt__(other)

    def is_null(self):
        """Return whether or not this is a null transaction"""
        return self._value == 0 and self._description is None

    def value(self):
        """Return the value of this transaction. This will be always greater
           than or equal to zero
        """
        return self._value

    def description(self):
        """Return the description of this transaction"""
        return self._description

    @staticmethod
    def maximum_transaction_value():
        """Return the maximum value for a single transaction. Currently this
           is 999999.999999 so that a transaction fits into a f013.6 string
        """
        return _create_decimal(999999.999999)

    @staticmethod
    def round(value):
        """Round the passed floating point value to the precision
           level of the transaction (currently 6 decimal places)
        """
        return _create_decimal(value)

    @staticmethod
    def split(value, description):
        """Split the passed transaction described by 'description' with value
           'value' into a list of transactions that fit the maximum transaction
           limit.
        """
        value = _create_decimal(value)

        if value < Transaction.maximum_transaction_value():
            t = Transaction(value, description)
            return [t]
        else:
            orig_value = value
            values = []

            while value > Transaction.maximum_transaction_value():
                values.append(Transaction.maximum_transaction_value())
                value -= Transaction.maximum_transaction_value()

            if value > 0:
                values.append(value)

            total = 0
            for value in values:
                total += value

            if total != orig_value:
                values[-1] -= (total - orig_value)

            transactions = []

            for i in range(0, len(values)):
                transactions.append(Transaction(values[i], "%s: %d of %d" %
                                    (description, i+1, len(values))))

            values = None

            total = 0
            for transaction in transactions:
                total += transaction.value()

            # ensure that the total is also rounded to 6 dp
            total = _create_decimal(total)

            if total != orig_value:
                raise TransactionError(
                    "Error as split sum (%s) is not equal to the original "
                    "value (%s)" % (total, orig_value))

            return transactions

    @staticmethod
    def from_data(data):
        """Return a newly constructed transaction from the passed dictionary
           that has been decoded from json
        """
        transaction = Transaction()

        if (data and len(data) > 0):
            transaction._value = _create_decimal(_Decimal(data["value"]))
            transaction._description = data["description"]

        return transaction

    def to_data(self):
        """Return this transaction as a dictionary that can be encoded
           to json
        """
        data = {}

        if not self.is_null():
            data["value"] = str(self.value())
            data["description"] = self._description

        return data
