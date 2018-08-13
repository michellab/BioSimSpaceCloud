
from ._function import call_function as _call_function
from ._keys import PrivateKey as _PrivateKey

# If we can, import qrcode to auto-generate QR codes
# for the login url
try:
    import qrcode as _qrcode
    has_qrcode = True
except:
    has_qrcode = False

__all__ = ["User"]

class LoginError(Exception):
    pass

class User:
    """This class holds all functionality that would be used
       by a user to authenticate with and access the service.
       This represents a single client login, and is the 
       user-facing part of Acquire
    """

    def __init__(self, username):
        """Construct a null user"""
        self._username = username
        self._session_key = None
        self._signing_key = None

    def sessionKey(self):
        """Return the session key for the current login session"""
        return self._session_key

    def signingKey(self):
        """Return the signing key used for the current login session"""
        return self._signing_key

    def loginURL(self):
        """Return the URL that the user must connect to to authenticate 
           this login session"""
        try:
            return self._login_url
        except:
            return None

    def loginQRCode(self):
        """Return a QR code of the login URL that the user must connect to
           to authenticate this login session"""
        try:
            return self._login_qrcode
        except:
            return None

    def isLoggedIn(self):
        """Return whether or not the user has successfully logged in"""
        return False

    def requestLogin(self, identity_url=None):
        """Connect to the identity URL 'identity_url'
           and request a login to the account connected to 
           'username'. This returns a login URL that you must
           connect to to supply your login credentials

           If 'identity_url' is None then it is discovered
           from the system
        """

        if not self._session_key is None:
            raise LoginError("You cannot try to log in twice...")

        if identity_url is None:
            # eventually we need to discover this from the system...
            identity_url = "http://130.61.60.88:8080/r/identity/request-login"

        # first, create a private key that will be used
        # to sign all requests and identify this login
        session_key = _PrivateKey()
        signing_key = _PrivateKey()

        # we will send the public key to the authentication
        # service so that it can validate all future communication
        # and requests
        pubkey = session_key.public_key().bytes() \
                            .decode("utf-8")

        certkey = signing_key.public_key().bytes() \
                             .decode("utf-8")

        result = _call_function(identity_url, {"username" : self._username,
                                               "public_key" : pubkey,
                                               "public_certificate" : certkey,
                                               "ipaddr" : "somewhere" })

        # look for status = 0
        try:
            status = int( result["status"] )
        except:
            status = -1

        try:
            message = result["message"]
        except:
            message = str(result)

        if status !=0:
            raise LoginError("Failed to login. Error = %d. Message = %s" % \
                                (status, message))

        try:
            login_url = result["login_url"]
        except:
            login_url = None

        if login_url is None:
            raise LoginError("Failed to login. Could not extract the login URL! "
                             "Result is %s" % (str(result)))

        # now save all of the needed data
        self._login_url = result["login_url"]
        self._identity_url = identity_url
        self._session_key = session_key
        self._signing_key = signing_key

        qrcode = None

        if has_qrcode:
            try:
                self._login_qrcode = _qrcode.make(self._login_url)
                qrcode = self._login_qrcode
            except:
                pass

        return (self._login_url,qrcode)
