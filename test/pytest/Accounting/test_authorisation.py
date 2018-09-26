
from Acquire.Accounting import Authorisation

from Acquire.Crypto import PrivateKey, PublicKey

import pytest
import uuid


def test_authorisation():
    key = PrivateKey()

    account_uid = uuid.uuid4()

    auth = Authorisation(account_uid=account_uid, testing_key=key)

    auth.verify(account_uid=account_uid, testing_key=key.public_key())

    wrong_key = PrivateKey()

    with pytest.raises(PermissionError):
        auth.verify(account_uid=account_uid,
                    testing_key=wrong_key.public_key())

    wrong_uid = uuid.uuid4()

    with pytest.raises(PermissionError):
        auth.verify(account_uid=wrong_uid, testing_key=key.public_key())

    data = auth.to_data()

    new_auth = Authorisation.from_data(data)

    new_auth.verify(account_uid=account_uid, testing_key=key.public_key())

    with pytest.raises(PermissionError):
        new_auth.verify(account_uid=account_uid,
                        testing_key=wrong_key.public_key())

    with pytest.raises(PermissionError):
        new_auth.verify(account_uid=wrong_uid, testing_key=key.public_key())
