
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

    data = t.to_data()
    t2 = Transaction.from_data(data)

    assert(t.value() == t2.value())
    assert(t.description() == t2.description())
    assert(t == t2)


@pytest.mark.parametrize("value",
                         [0.1, 0.5, 6.434323])
def test_descriptionless_fails(value):
    with pytest.raises(TransactionError):
        t = Transaction(value)
        assert(t.is_null())


@pytest.mark.parametrize("value",
                         [-0.5, -3.564, -0.000001])
def test_negative_fails(value):
    with pytest.raises(TransactionError):
        t = Transaction(value, "this is a negative transaction")
        assert(t.is_null())


@pytest.mark.parametrize("value1, value2",
                         [(0.5, 0.8), (10, 20), (0, 0.000001)])
def test_comparison(value1, value2):
    t1 = Transaction(value1, "lower")
    t2 = Transaction(value2, "higher")

    assert(t1 < t2)
    assert(t2 > t1)
    assert(t1 < value2)
    assert(t2 > value1)
    assert(t1 >= value1)
    assert(t1 <= value1)
    assert(t2 >= value2)
    assert(t2 <= value2)
    assert(t1 == value1)
    assert(t2 == value2)
    assert(t1 == t1)
    assert(t2 == t2)
    assert(t1 != t2)
    assert(t2 != t1)
    assert(t1 != value2)
    assert(t2 != value1)


@pytest.mark.parametrize("value", [0, 1000, 1000000, 1023898493,
                                   490294320.8594085093])
def test_split(value):
    transactions = Transaction.split(value, "something")

    total = 0
    for transaction in transactions:
        total += transaction.value()

    total = Transaction.round(total)

    assert(total == Transaction.round(value))
