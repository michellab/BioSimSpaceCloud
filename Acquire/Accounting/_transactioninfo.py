
from enum import Enum as _Enum

from ._decimal import create_decimal as _create_decimal

__all__ = ["TransactionInfo", "TransactionCode"]


class TransactionCode(_Enum):
    CREDIT = "CR"
    DEBIT = "DR"
    CURRENT_LIABILITY = "CL"
    ACCOUNT_RECEIVABLE = "AR"
    RECEIVED_RECEIPT = "RR"
    SENT_RECEIPT = "SR"
    RECEIVED_REFUND = "RF"
    SENT_REFUND = "SF"


class TransactionInfo:
    """This class is used to encode and extract the type of transaction
       and value to/from an object store key
    """
    def __init__(self, key):
        """Extract information from the passed object store key.
           This looks for the string in the key that matches
           '2 letters followed by a number'

           CL000100.005000
           DR000004.234100

           etc.

           This is a two-letter code that describes the type
           of transaction, together with the value
        """

        parts = key.split("/")

        # start at the end...
        for i in range(-1, -len(parts), -1):
            part = parts[i]

            try:
                code = TransactionInfo._get_code(part[0:2])
                value = _create_decimal(part[2:])

                self._code = code
                self._value = value
                return
            except:
                pass

        raise ValueError("Cannot extract transaction info from '%s'" % key)

    def __str__(self):
        return "TransactionInfo(code==%s, value==%s)" % \
                    (self._code.value, self._value)

    @staticmethod
    def _get_code(code):
        """Return the TransactionCode matching 'code'"""
        return TransactionCode(code)

    @staticmethod
    def encode(code, value, original_value=None):
        """Encode the passed code and value into a simple string that can
           be used as part of an object store key. If 'original_value' is
           passed, then encode the original value of the provisional
           transaction too
        """
        return "%2s%013.6f" % (code.value, value)

    def value(self):
        """Return the value of the transaction"""
        return self._value

    def original_value(self):
        """Return the original value of the provisional transaction"""
        return self._value

    def is_credit(self):
        """Return whether or not this is a credit"""
        return self._code == TransactionCode.CREDIT

    def is_debit(self):
        """Return whether or not this is a debit"""
        return self._code == TransactionCode.DEBIT

    def is_liability(self):
        """Return whether or not this is a liability"""
        return self._code == TransactionCode.CURRENT_LIABILITY

    def is_accounts_receivable(self):
        """Return whether or not this is accounts receivable"""
        return self._code == TransactionCode.ACCOUNT_RECEIVABLE

    def is_sent_receipt(self):
        """Return whether or not this is a sent receipt"""
        return self._code == TransactionCode.SENT_RECEIPT

    def is_received_receipt(self):
        """Return whether or not this is a received receipt"""
        return self._code == TransactionCode.RECEIVED_RECEIPT

    def is_sent_refund(self):
        """Return whether or not this is a sent refund"""
        return self._code == TransactionCode.SENT_REFUND

    def is_received_refund(self):
        """Return whether or not this is a received refund"""
        return self._code == TransactionCode.RECEIVED_REFUND
