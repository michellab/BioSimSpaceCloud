
from ._function import call_function as _call_function
from ._keys import PrivateKey as _PrivateKey

import os as _os

from enum import Enum as _Enum

from datetime import datetime as _datetime
import time as _time

# If we can, import qrcode to auto-generate QR codes
# for the login url
try:
    import qrcode as _qrcode
    has_qrcode = True
except:
    has_qrcode = False

# If we can, import socket to get the hostname and IP address
try:
    import socket as _socket
    has_socket = True
except:
    has_socket = False

__all__ = ["User"]

class LoginError(Exception):
    pass

class _LoginStatus(_Enum):
    EMPTY = 0
    LOGGING_IN = 1
    LOGGED_IN = 2
    LOGGED_OUT = 3
    ERROR = 4

class User:
    """This class holds all functionality that would be used
       by a user to authenticate with and access the service.
       This represents a single client login, and is the 
       user-facing part of Acquire
    """

    def __init__(self, username):
        """Construct a null user"""
        self._username = username
        self._status = _LoginStatus.EMPTY

    def __enter__(self):
        """Enter function used by 'with' statements'"""
        pass

    def __exit__(self):
        """Ensure that we logout"""
        self.logout()

    def __del__(self):
        """Make sure that we log out before deleting this object"""
        self.logout()

    def _setStatus(self, status):
        """Internal function used to set the status from the 
           string obtained from the LoginSession"""

        if status == "approved":
            self._status = _LoginStatus.LOGGED_IN
        elif status == "denied":
            self._setErrorState("Permission to log in was denied!")
        elif status == "logged_out":
            self._status = _LoginStatus.LOGGED_OUT

    def status(self):
        """Return the current status of this account"""
        return self._status

    def _checkForError(self):
        """Call to ensure that this object is not in an error
           state. If it is in an error state then raise an
           exception"""
        if self._status == _LoginStatus.ERROR:
            raise LoginError(self._error_string)

    def _setErrorState(self, message):
        """Put this object into an error state, displaying the
           passed message if anyone tries to use this object"""
        self._status = _LoginStatus.ERROR
        self._error_string = message

    def sessionKey(self):
        """Return the session key for the current login session"""
        self._checkForError()

        try:
            return self._session_key
        except:
            return None

    def signingKey(self):
        """Return the signing key used for the current login session"""
        self._checkForError()

        try:
            return self._signing_key
        except:
            return None

    def identityServiceURL(self):
        """Return the URL to the identity service. This is the full URL
           to the service, minus the actual function to be called, e.g.
           https://function_service.com/r/identity
        """
        self._checkForError()

        try:
            return self._identity_url
        except:
            return None

    def loginURL(self):
        """Return the URL that the user must connect to to authenticate 
           this login session"""
        self._checkForError()

        try:
            return self._login_url
        except:
            return None

    def loginQRCode(self):
        """Return a QR code of the login URL that the user must connect to
           to authenticate this login session"""
        self._checkForError()

        try:
            return self._login_qrcode
        except:
            return None

    def sessionUID(self):
        """Return the UID of the current login session. Returns None
           if there is no valid login session"""
        self._checkForError()

        try:
            return self._session_uid
        except:
            return None

    def isEmpty(self):
        """Return whether or not this is an empty login (so has not
           been used for anything yet..."""
        return self._status == _LoginStatus.EMPTY

    def isLoggedIn(self):
        """Return whether or not the user has successfully logged in"""
        return self._status == _LoginStatus.LOGGED_IN

    def isLoggingIn(self):
        """Return whether or not the user is in the process of loggin in"""
        return self._status == _LoginStatus.LOGGING_IN

    def logout(self):
        """Log out from the current session"""
        if self.isLoggedIn() or self.isLoggingIn():
            pass

    def requestLogin(self, login_message=None, identity_url=None):
        """Connect to the identity URL 'identity_url'
           and request a login to the account connected to 
           'username'. This returns a login URL that you must
           connect to to supply your login credentials

           If 'login_message' is supplied, then this is passed to
           the identity service so that it can be displayed
           when the user accesses the login page. This helps
           the user validate that they have accessed the correct
           login page. Note that if the message is None,
           then a random message will be generated.

           If 'identity_url' is None then it is discovered
           from the system
        """
        self._checkForError()

        if not self.isEmpty():
            raise LoginError("You cannot try to log in twice using the same "
                             "User object. Create another object if you want "
                             "to try to log in again.")

        if identity_url is None:
            # eventually we need to discover this from the system...
            identity_url = "http://130.61.60.88:8080/r/identity"

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

        args = { "username" : self._username,
                 "public_key" : pubkey,
                 "public_certificate" : certkey,
                 "ipaddr" : None }

        # get information from the local machine to help
        # the user validate that the login details are correct
        if has_socket:
            hostname = _socket.gethostname()
            ipaddr = _socket.gethostbyname(hostname)
            args["ipaddr"] = ipaddr
            args["hostname"] = hostname

        if login_message is None:
            login_message = "User '%s' in process '%s' wants to log in..." % \
                              (_os.getlogin(),_os.getpid())

        args["message"] = login_message

        result = _call_function("%s/request-login" % identity_url, args)

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
            error = "Failed to login. Error = %d. Message = %s" % \
                                (status, message)
            self._setErrorState(error)
            raise LoginError(error)

        try:
            login_url = result["login_url"]
        except:
            login_url = None

        if login_url is None:
            error = "Failed to login. Could not extract the login URL! " % \
                             "Result is %s" % (str(result))
            self._setErrorState(error)
            raise LoginError(error)

        try:
            session_uid = result["session_uid"]
        except:
            session_uid = None

        if session_uid is None:
            error = "Failed to login. Could not extract the login " \
                    "session UID! Result is %s" % (str(result))

            self._setErrorState(error)
            raise LoginError(error)

        # now save all of the needed data
        self._login_url = result["login_url"]
        self._identity_url = identity_url
        self._session_key = session_key
        self._signing_key = signing_key
        self._session_uid = session_uid
        self._status = _LoginStatus.LOGGING_IN

        qrcode = None

        if has_qrcode:
            try:
                self._login_qrcode = _qrcode.make(self._login_url)
                qrcode = self._login_qrcode
            except:
                pass

        return (self._login_url,qrcode)

    def _pollSessionStatus(self):
        """Function used to query the identity service for this session
           to poll for the session status"""

        identity_url = self.identityServiceURL()

        if identity_url is None:
            return

        args = { "username" : self._username,
                 "session_uid" : self._session_uid }

        result = _call_function("%s/get-status" % identity_url, args)

        print(result)
	    
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
            error = "Failed to query identity service. Error = %d. Message = %s" % \
                                (status, message)
            self._setErrorState(error)
            raise LoginError(error)

        # now update the status...
        status = result["session_status"]
        self._setStatus(status)

    def waitForLogin(self, timeout=None, polling_delta=5):
        """Block until the user has logged in. If 'timeout' is set
           then we will wait for a maximum of that number of seconds

           This will check whether we have logged in by polling
           the identity service every 'polling_delta' seconds.
        """

        self._checkForError()

        if not self.isLoggingIn():
            return self.isLoggedIn()

        polling_delta = int(polling_delta)
        if polling_delta > 60:
            polling_delta = 60
        elif polling_delta < 1:
            polling_delta = 1

        if timeout is None:
            # block forever....
            while True:
                self._pollSessionStatus()

                if self.isLoggedIn():
                    return True

                elif not self.isLoggingIn():
                    return False

                _time.sleep(polling_delta)
        else:
            # only block until the timeout has been reached
            timeout = int(timeout)
            if timeout < 1:
                timeout = 1

            start_time = _datetime.now()

            while (_datetime.now() - start_time).seconds < timeout:
                self._pollSessionStatus()

                if self.isLoggedIn():
                    return True

                elif not self.isLoggingIn():
                    return False

                _time.sleep(polling_delta)

            return False
