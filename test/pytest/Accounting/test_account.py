
import pytest
import os
import random

from Acquire.Accounting import Account, Transaction, TransactionRecord, \
                               Authorisation, create_decimal

from Acquire.Service import login_to_service_account

account1_overdraft_limit = 1500
account2_overdraft_limit = 2500


@pytest.fixture(scope="module")
def bucket(tmpdir_factory):
    d = tmpdir_factory.mktemp("objstore")
    return login_to_service_account(str(d))


@pytest.fixture(scope="module")
def account1(bucket):
    account = Account("Testing Account", "This is the test account")
    uid = account.uid()
    assert(uid is not None)
    assert(account.balance() == 0)
    assert(account.liability() == 0)

    account.set_overdraft_limit(account1_overdraft_limit)
    assert(account.get_overdraft_limit() == account1_overdraft_limit)

    return account


@pytest.fixture(scope="module")
def account2(bucket):
    account = Account("Testing Account", "This is a second testing account")
    uid = account.uid()
    assert(uid is not None)
    assert(account.balance() == 0)
    assert(account.liability() == 0)

    account.set_overdraft_limit(account2_overdraft_limit)
    assert(account.get_overdraft_limit() == account2_overdraft_limit)

    return account


@pytest.fixture(params=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
def random_transaction(account1, account2):
    value = create_decimal(1000.0 * random.random())
    description = "%s transaction" % value
    transaction = Transaction(value, description)

    assert(transaction.value() == value)
    assert(transaction.description() == description)

    assert(account1.get_overdraft_limit() == account1_overdraft_limit)
    assert(account2.get_overdraft_limit() == account2_overdraft_limit)

    if random.randint(0, 1):
        return (transaction, account1, account2)
    else:
        return (transaction, account2, account1)


def test_account(bucket):
    name = "test account"
    description = "This is a test account"

    account = Account(name, description)

    assert(account.name() == name)
    assert(account.description() == description)
    assert(not account.is_null())

    uid = account.uid()
    assert(uid is not None)

    account2 = Account(uid=uid)

    assert(account2.name() == name)
    assert(account2.description() == description)

    assert(account.balance() == 0)


def test_transactions(random_transaction):
    (transaction, account1, account2) = random_transaction

    starting_balance1 = account1.balance()
    starting_liability1 = account1.liability()

    starting_balance2 = account2.balance()
    starting_liability2 = account2.liability()

    TransactionRecord.perform(transaction, account1, account2,
                              Authorisation(), is_provisional=False)

    ending_balance1 = account1.balance()
    ending_liability1 = account1.liability()

    ending_balance2 = account2.balance()
    ending_liability2 = account2.liability()

    assert(ending_balance1 == starting_balance1 - transaction.value())
    assert(ending_balance2 == starting_balance2 + transaction.value())

    assert(ending_liability1 == starting_liability1)
    assert(starting_liability2 == ending_liability2)
