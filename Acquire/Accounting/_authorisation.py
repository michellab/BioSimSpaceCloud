
from Acquire.ObjectStore import bytes_to_string as _bytes_to_string
from Acquire.ObjectStore import string_to_bytes as _string_to_bytes

__all__ = ["Authorisation"]


class Authorisation:
    """This class holds the information needed to authorise a transaction
       in an account
    """
    def __init__(self, session_uid=None, signing_key=None):
        if session_uid is not None:
            self._session_uid = str(session_uid)
        else:
            self._session_uid = None

        if signing_key is not None:
            self._signature = signing_key.sign(self._session_uid)
        else:
            self._signature = None

    def __str__(self):
        try:
            return "Authorisation(session_uid=%s)" % self._session_uid
        except:
            return "Authorisation()"

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._session_uid == other._session_uid and \
                   self._signature == other._signature
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def session_uid(self):
        """Return the UID of the login session that was used to provide
           this authentication
        """
        return self._session_uid

    def verify(self, signing_key):
        """Verify that this authorisation was signed by the passed
           signing key
        """
        signing_key.verify(self._signature, self._session_uid)

    @staticmethod
    def from_data(data):
        """Return an authorisation created from the json-decoded dictionary"""
        auth = Authorisation()

        if (data and len(data) > 0):
            auth._session_uid = data["session_uid"]

            try:
                auth._signature = _string_to_bytes(data["signature"])
            except:
                auth._signature = None

        return auth

    def to_data(self):
        """Return this object serialised to a json-encoded dictionary"""
        data = {}

        if self._session_uid:
            data["session_uid"] = self._session_uid

        if self._signature:
            data["signature"] = _bytes_to_string(self._signature)

        return data
