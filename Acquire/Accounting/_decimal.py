
from decimal import Decimal as _Decimal
from decimal import Context as _Context

from ._errors import AccountError

__all__ = ["create_decimal", "get_decimal_context"]


def get_decimal_context():
    """Return the context used for all decimals in transactions. This
       context rounds to 6 decimal places and provides sufficient precision
       to support any value between 0 and 999,999,999,999,999.999,999,999
       (i.e. everything up to just under one quadrillion - I doubt we will
        ever have an account that has more than a trillion units in it!)
    """
    return _Context(prec=24)


def create_decimal(value):
    """Create a decimal from the passed value. This is a decimal that
       has 6 decimal places and is clamped between
       -1 quadrillion < value < 1 quadrillion
    """
    try:
        d = _Decimal("%.6f" % value, get_decimal_context())
    except:
        value = _Decimal(value, get_decimal_context())
        d = _Decimal("%.6f" % value, get_decimal_context())

    if d <= -1000000000000:
        raise AccountError(
                "You cannot create a balance with a value less than "
                "-1 quadrillion! (%s)" % (value))

    elif d >= 1000000000000000:
        raise AccountError(
                "You cannot create a balance with a value greater than "
                "1 quadrillion! (%s)" % (value))

    return d
