
import pytest

from Acquire.Accounting import Transaction, TransactionError


def test_transaction_is_null():
    t = Transaction()
    assert(t.is_null())


@pytest.mark.parametrize("value, description",
                        [(0.5, "hello",),
                         (7.123456, "goodbye"),
                         (0.000001, "something is here!")])
def test_transaction_value(value, description):
    t = Transaction(value, description)
    assert(t.value() == value)
    assert(t.description() == description)


@pytest.mark.parametrize("value",
                         [0.1, 0.5, 6.434323])
def test_descriptionless_fails(value):
    with pytest.raises(TransactionError):
        t = Transaction(value)


@pytest.mark.parametrize("value",
                         [-0.5, -3.564, -0.000001])
def test_negative_fails(value):
    with pytest.raises(TransactionError):
        t = Transaction(value, "this is a negative transaction")

