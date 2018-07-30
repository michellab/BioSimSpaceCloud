
from ._function import call_function as _call_function

from ._keys import PrivateKey as _PrivateKey

__all__ = ["User"]

class LoginError(Exception):
    pass

class User:
    """This class holds all functionality that would be used
       by a user to authenticate with and access the service
    """

    def __init__(self, username):
        """Construct a null user"""
        self._username = username
        self._session_key = None
        self._signing_key = None

    def requestLogin(self,auth_url):
        """Connect to the authentication URL at 'auth_url'
           and request a login to the account connected to 
           'username'. This will return a User object that 
           will hold all keys that will represent this login
        """

        if not self._session_key is None:
            raise LoginError("You cannot try to log in twice...")

        # first, create a private key that will be used
        # to sign all requests and identify this login
        self._session_key = _PrivateKey()
        self._signing_key = _PrivateKey()

        # we will send the public key to the authentication
        # service so that it can validate all future communication
        # and requests
        pubkey = self._session_key.public_key().bytes() \
                                  .decode("utf-8")

        certkey = self._signing_key.public_key().bytes() \
                                   .decode("utf-8")

        result = _call_function(auth_url, {"username" : self._username,
                                           "public_key" : pubkey,
                                           "public_certificate" : certkey,
                                           "ipaddr" : "somewhere" })

        return result
