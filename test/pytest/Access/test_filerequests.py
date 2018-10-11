
from Acquire.Access import Request, FileWriteRequest
from Acquire.Crypto import PrivateKey

import pytest
import os
import hashlib


def test_filewriterequest():
    basedir = os.path.dirname(os.path.abspath(__file__))

    filenames = [os.path.abspath(__file__),
                 os.path.abspath("%s/../Accounting/test_account.py" % basedir)]

    testkey = PrivateKey()

    r = FileWriteRequest(filenames=filenames, testing_key=testkey)

    data = r.to_data()

    r2 = Request.from_data(data)

    assert(r == r2)
    assert(r.uid() == r2.uid())

    for i, filename in enumerate(filenames):
        md5sum = hashlib.md5(open(filename, "rb").read()).hexdigest()
        assert(md5sum == r.checksums()[i])

    r.authorisation().verify(r.resource_key(),
                             testing_key=testkey.public_key())
