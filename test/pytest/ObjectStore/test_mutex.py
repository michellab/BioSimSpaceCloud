
from Acquire.ObjectStore import Mutex, MutexTimeoutError
from Acquire.Service import login_to_service_account

import datetime
import pytest


@pytest.fixture(scope="module")
def bucket(tmpdir_factory):
    d = tmpdir_factory.mktemp("objstore")
    return login_to_service_account(str(d))


def test_mutex(bucket):
    m = Mutex("ObjectStore.test_mutex")

    assert(m.is_locked())
    m.unlock()
    assert(not m.is_locked())
    m.lock()
    assert(m.is_locked())
    m.lock()
    assert(m.is_locked())
    m.unlock()
    assert(m.is_locked())
    m.unlock()
    assert(not m.is_locked())

    m2 = Mutex("ObjectStore.test_mutex")
    assert(m2.is_locked())

    with pytest.raises(MutexTimeoutError):
        m.lock(timeout=datetime.timedelta(seconds=1))

    assert(not m.is_locked())
    assert(m2.is_locked())

    m2.unlock()
    m.lock()

    assert(m.is_locked())
    assert(not m2.is_locked())
