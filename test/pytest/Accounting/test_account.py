
import pytest
import os

from Acquire.Accounting import Account, Transaction, TransactionRecord, \
                               Authorisation

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


def test_transactions(account1, account2):
    starting_balance1 = account1.balance()
    starting_liability1 = account1.liability()
    assert(account1.get_overdraft_limit() == account1_overdraft_limit)

    starting_balance2 = account2.balance()
    starting_liability2 = account2.liability()
    assert(account2.get_overdraft_limit() == account2_overdraft_limit)

    transaction = Transaction(100.005, "Test transaction")

    TransactionRecord.perform(transaction, account1, account2,
                              Authorisation(), is_provisional=True)

    ending_balance1 = account1.balance()
    ending_liability1 = account1.liability()

    ending_balance2 = account2.balance()
    ending_liability2 = account2.liability()

    assert(ending_balance1 == starting_balance1)
    assert(ending_balance2 == starting_balance2)

    assert(ending_liability1 - starting_liability1 == transaction.value())
    assert(starting_liability2 - ending_liability2 == transaction.value())
