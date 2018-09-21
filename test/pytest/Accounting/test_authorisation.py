
from Acquire.Accounting import Authorisation

from Acquire.Crypto import PrivateKey, PublicKey, SignatureVerificationError

import pytest
import uuid


def test_authorisation():
    key = PrivateKey()

    session_uid = uuid.uuid4()

    auth = Authorisation(session_uid=session_uid, signing_key=key)

    auth.verify(key.public_key())

    wrong_key = PrivateKey()

    with pytest.raises(SignatureVerificationError):
        auth.verify(wrong_key.public_key())

    data = auth.to_data()

    new_auth = Authorisation.from_data(data)

    new_auth.verify(key.public_key())

    with pytest.raises(SignatureVerificationError):
        auth.verify(wrong_key.public_key())

    assert(new_auth.session_uid() == auth.session_uid())
    assert(new_auth.session_uid() == str(session_uid))
