
import pytest
import os

from Acquire.Accounting import Account
from Acquire.Service import login_to_service_account


@pytest.fixture(scope="module")
def bucket(tmpdir_factory):
    d = tmpdir_factory.mktemp("objstore")
    bucket = login_to_service_account(str(d))
    return bucket


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
