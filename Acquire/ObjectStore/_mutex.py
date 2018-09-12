
import uuid
import datetime as _datetime

from ._objstore import ObjectStore as _ObjectStore

from ._errors import MutexTimeoutError

__all__ = ["Mutex"]


class Mutex:
    """This class implements a mutex that sits in the object store.
       The mutex is associated with a key. A thread holds this mutex
       if it has successfully written its secret to this key. If
       not, then another thread must hold the mutex, and we have
       to wait...
    """
    def __init__(self, key=None, timeout=None, bucket=None):
        """Create the mutex. The immediately tries to lock the mutex
           for key 'key' and will block until a lock is successfully
           obtained (or until 'timeout' has been reached, and an
           exception is then thrown). If not key is provided, then
           this is the (single) global mutex
        """
        if key is None:
            key = "mutexes/none"
        else:
            key = "mutexes/%s" % str(key).replace(" ", "_")

        if bucket is None:
            from Acquire.Service import login_to_service_account as \
                                       _login_to_service_account

            bucket = _login_to_service_account()

        self._bucket = bucket
        self._key = key
        self._secret = str(uuid.uuid4())
        self._is_locked = 0
        self.lock(timeout)

    def __del__(self):
        """Release the mutex if it is held"""
        while self.is_locked():
            self.unlock()

    def is_locked(self):
        """Return whether or not this mutex is locked"""
        return self._is_locked > 0

    def unlock(self):
        """Release the mutex if it is held. Does nothing if the mutex
           is not held
        """
        if not self.is_locked():
            return

        if self._is_locked > 1:
            self._is_locked -= 1
            return

        try:
            holder = _ObjectStore.get_string_object(self._bucket, self._key)
        except:
            holder = None

        if holder == self._lockstring:
            # we hold the mutex - delete the key
            _ObjectStore.delete_object(self._bucket, self._key)

        self._is_locked = False

    def lock(self, timeout=None):
        """Lock the mutex, blocking until the mutex is held, or until
           'timeout' has passed. If we time out, then an exception is
           raised
        """
        if self.is_locked():
            self._is_locked += 1
            return

        now = _datetime.datetime.now()

        # if the user does not provide a timeout, then we will set a timeout
        # of at most 1 minute
        if timeout is None:
            endtime = now + _datetime.timedelta(minutes=1)
        else:
            endtime = now + timeout

        # This is the first time we are trying to get a lock
        while now < endtime:
            # does anyone else hold the lock?
            try:
                holder = _ObjectStore.get_string_object(self._bucket,
                                                        self._key)
            except:
                holder = None

            if holder is None:
                # no-one holds this mutex - try to hold it now
                self._lockstring = "%s %s" % (self._secret, now.timestamp())

                _ObjectStore.set_string_object(self._bucket, self._key,
                                               self._lockstring)

                holder = _ObjectStore.get_string_object(self._bucket,
                                                        self._key)
            else:
                self._lockstring = None

            if holder == self._lockstring:
                # it looks like we are the holder - read and write again
                # just to make sure
                holder = _ObjectStore.get_string_object(self._bucket,
                                                        self._key)

                if holder == self._lockstring:
                    # write again just to make sure
                    _ObjectStore.set_string_object(self._bucket, self._key,
                                                   self._lockstring)

                    holder = _ObjectStore.get_string_object(self._bucket,
                                                            self._key)

            if holder == self._lockstring:
                # we have read and written our secret to the object store
                # three times. While a race condition is still possible,
                # I'd hope it is now highly unlikely - we now hold the mutex
                self._is_locked = 1
                return

            now = _datetime.datetime.now()

        raise MutexTimeoutError("Cannot acquire a mutex lock on the "
                                "key '%s'" % self._key)
