
import pytest
import random
import datetime

from Acquire.Accounting import Account, Transaction, TransactionRecord, \
                               Ledger, Authorisation, Receipt, Refund, \
                               create_decimal

from Acquire.Service import login_to_service_account

try:
    from freezegun import freeze_time
    have_freezetime = True
except:
    have_freezetime = False

account1_overdraft_limit = 1500000
account2_overdraft_limit = 2500000

start_time = datetime.datetime.now() - datetime.timedelta(days=365)


@pytest.fixture(scope="module")
def bucket(tmpdir_factory):
    d = tmpdir_factory.mktemp("objstore")
    return login_to_service_account(str(d))


@pytest.fixture(scope="module")
def account1(bucket):
    if not have_freezetime:
        return None

    with freeze_time(start_time) as frozen_datetime:
        now = datetime.datetime.now()
        assert(frozen_datetime() == now)
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
    if not have_freezetime:
        return None

    with freeze_time(start_time) as frozen_datetime:
        now = datetime.datetime.now()
        assert(frozen_datetime() == now)
        account = Account("Testing Account", "This is the test account")

        uid = account.uid()
        assert(uid is not None)
        assert(account.balance() == 0)
        assert(account.liability() == 0)

        account.set_overdraft_limit(account2_overdraft_limit)
        assert(account.get_overdraft_limit() == account2_overdraft_limit)

    return account


def test_temporal_transactions(account1, account2):
    if not have_freezetime:
        return

    zero = create_decimal(0)

    balance1 = zero
    balance2 = zero
    final_balance1 = zero
    final_balance2 = zero
    liability1 = zero
    liability2 = zero
    receivable1 = zero
    receivable2 = zero

    # generate some random times for the transactions
    random_dates = []
    now = datetime.datetime.now()
    for i in range(0, 100):
        random_dates.append(start_time + random.random() * (now - start_time))

    # (which must be applied in time order!)
    random_dates.sort()

    records = []

    for transaction_time in random_dates:
        with freeze_time(transaction_time) as frozen_datetime:
            now = datetime.datetime.now()
            assert(frozen_datetime() == now)

            is_provisional = random.randint(0, 5)

            transaction = Transaction(25*random.random(),
                                      "test transaction %d" % i)
            auth = Authorisation()

            if random.randint(0, 10):
                record = Ledger.perform(transaction, account1, account2,
                                        auth, is_provisional)

                if is_provisional:
                    liability1 += transaction.value()
                    receivable2 += transaction.value()
                else:
                    balance1 -= transaction.value()
                    balance2 += transaction.value()

                final_balance1 -= transaction.value()
                final_balance2 += transaction.value()
            else:
                record = Ledger.perform(transaction, account2, account1,
                                        auth, is_provisional)

                if is_provisional:
                    receivable1 += transaction.value()
                    liability2 += transaction.value()
                else:
                    balance1 += transaction.value()
                    balance2 -= transaction.value()

                final_balance1 += transaction.value()
                final_balance2 -= transaction.value()

            if is_provisional:
                records.append(record)

            assert(record.timestamp() == now.timestamp())

    assert(account1.balance() == balance1)
    assert(account2.balance() == balance2)
    assert(account1.liability() == liability1)
    assert(account1.receivable() == receivable1)
    assert(account2.liability() == liability2)
    assert(account2.receivable() == receivable2)

    for record in records:
        Ledger.receipt(Receipt(record.credit_note(), Authorisation()),
                       bucket=bucket)

    assert(account1.balance() == final_balance1)
    assert(account2.balance() == final_balance2)

    assert(account1.liability() == zero)
    assert(account1.receivable() == zero)
    assert(account2.liability() == zero)
    assert(account2.receivable() == zero)
