
from ._function import call_function as _call_function
from ._function import bytes_to_string as _bytes_to_string
from ._function import string_to_bytes as _string_to_bytes

from ._keys import PrivateKey as _PrivateKey

from ._qrcode import create_qrcode as _create_qrcode
from ._qrcode import has_qrcode as _has_qrcode

import os as _os

from enum import Enum as _Enum

from datetime import datetime as _datetime
import time as _time

# If we can, import socket to get the hostname and IP address
try:
    import socket as _socket
    _has_socket = True
except:
    _has_socket = False

__all__ = [ "User", "username_to_uuid", "uuid_to_username" ]

class LoginError(Exception):
    pass

class AccountError(Exception):
    pass

class _LoginStatus(_Enum):
    EMPTY = 0
    LOGGING_IN = 1
    LOGGED_IN = 2
    LOGGED_OUT = 3
    ERROR = 4

def _get_identity_url():
    """Function to discover and return the default identity url"""
    return "http://130.61.60.88:8080/r/identity"

def uuid_to_username(uuid, identity_url=None):
    """Function to return the username for the passed uuid"""
    if identity_url is None:
        identity_url = _get_identity_url()

    response = _call_function("%s/whois" % identity_url,
                              {"uuid" : str(uuid)})

    return response["username"]

def username_to_uuid(username, identity_url=None):
    """Function to return the uuid for the passed username"""
    if identity_url is None:
        identity_url = _get_identity_url()

    response = _call_function("%s/whois" % identity_url,
                              {"username" : username})

    return response["uuid"]

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

    def _set_status(self, status):
        """Internal function used to set the status from the 
           string obtained from the LoginSession"""

        if status == "approved":
            self._status = _LoginStatus.LOGGED_IN
        elif status == "denied":
            self._setErrorState("Permission to log in was denied!")
        elif status == "logged_out":
            self._status = _LoginStatus.LOGGED_OUT

    def username(self):
        """Return the username of the user"""
        return self._username

    def status(self):
        """Return the current status of this account"""
        return self._status

    def _check_for_error(self):
        """Call to ensure that this object is not in an error
           state. If it is in an error state then raise an
           exception"""
        if self._status == _LoginStatus.ERROR:
            raise LoginError(self._error_string)

    def _set_error_state(self, message):
        """Put this object into an error state, displaying the
           passed message if anyone tries to use this object"""
        self._status = _LoginStatus.ERROR
        self._error_string = message

    def session_key(self):
        """Return the session key for the current login session"""
        self._check_for_error()

        try:
            return self._session_key
        except:
            return None

    def signing_key(self):
        """Return the signing key used for the current login session"""
        self._check_for_error()

        try:
            return self._signing_key
        except:
            return None

    def identity_service_url(self):
        """Return the URL to the identity service. This is the full URL
           to the service, minus the actual function to be called, e.g.
           https://function_service.com/r/identity
        """
        self._check_for_error()

        try:
            return self._identity_url
        except:
            # return the default URL - this should be discovered...
            return _get_identity_url()

    def login_url(self):
        """Return the URL that the user must connect to to authenticate 
           this login session"""
        self._check_for_error()

        try:
            return self._login_url
        except:
            return None

    def login_qr_code(self):
        """Return a QR code of the login URL that the user must connect to
           to authenticate this login session"""
        self._check_for_error()

        try:
            return self._login_qrcode
        except:
            return None

    def session_uid(self):
        """Return the UID of the current login session. Returns None
           if there is no valid login session"""
        self._check_for_error()

        try:
            return self._session_uid
        except:
            return None

    def is_empty(self):
        """Return whether or not this is an empty login (so has not
           been used for anything yet..."""
        return self._status == _LoginStatus.EMPTY

    def is_logged_in(self):
        """Return whether or not the user has successfully logged in"""
        return self._status == _LoginStatus.LOGGED_IN

    def is_logging_in(self):
        """Return whether or not the user is in the process of loggin in"""
        return self._status == _LoginStatus.LOGGING_IN

    def logout(self):
        """Log out from the current session"""
        if self.is_logged_in() or self.is_logging_in():	
            identity_url = self.identity_service_url()
            
            if identity_url is None:
                return

            # create a permission message that can be signed
            # and then validated by the user
            permission = "Log out request for %s" % self._session_uid
            signature = self.signing_key().sign(permission)
            
            args = { "username" : self._username,
	             "session_uid" : self._session_uid,
                     "permission" : permission,
                     "signature" : _bytes_to_string(signature) }
	    
            print("Logging out %s from session %s" % (self._username,self._session_uid))
            result = _call_function("%s/logout" % identity_url, args)
            print(result)
            return result

    def create_account(self, password, identity_url=None):
        """Request to create an account with the identity service running
           at 'identity_url', using the supplied 'password'. This will
           return a QR code that you must use immediately to add this
           account to a QR code generator"""

        if self._username is None:
            return None

        if identity_url is None:
            identity_url = _get_identity_url()

        args = { "username" : self._username,
                 "password" : password }

        result = _call_function("%s/register" % identity_url, args)

        try:
            provisioning_uri = result["provisioning_uri"]
        except:
            raise AccountError("Cannot create a new account for '%s' on "
                   "the identity service at '%s'!" % (self._username,identity_url))

        # return a QR code for the provisioning URI
        return (provisioning_uri,_create_qrcode(provisioning_uri))

    def request_login(self, login_message=None, identity_url=None):
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
        self._check_for_error()

        if not self.is_empty():
            raise LoginError("You cannot try to log in twice using the same "
                             "User object. Create another object if you want "
                             "to try to log in again.")

        if identity_url is None:
            identity_url = self.identity_service_url()

        # first, create a private key that will be used
        # to sign all requests and identify this login
        session_key = _PrivateKey()
        signing_key = _PrivateKey()

        # we will send the public key to the authentication
        # service so that it can validate all future communication
        # and requests
        pubkey = _bytes_to_string(session_key.public_key().bytes())
        certkey = _bytes_to_string(signing_key.public_key().bytes())

        args = { "username" : self._username,
                 "public_key" : pubkey,
                 "public_certificate" : certkey,
                 "ipaddr" : None }

        # get information from the local machine to help
        # the user validate that the login details are correct
        if _has_socket:
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

        try:
            prune_message = result["prune_message"]
            print("Pruning old sessions...\n%s" % "\n".join(prune_message))
        except:
            pass

        if status !=0:
            error = "Failed to login. Error = %d. Message = %s" % \
                                (status, message)
            self._set_error_state(error)
            raise LoginError(error)

        try:
            login_url = result["login_url"]
        except:
            login_url = None

        if login_url is None:
            error = "Failed to login. Could not extract the login URL! " % \
                             "Result is %s" % (str(result))
            self._set_error_state(error)
            raise LoginError(error)

        try:
            session_uid = result["session_uid"]
        except:
            session_uid = None

        if session_uid is None:
            error = "Failed to login. Could not extract the login " \
                    "session UID! Result is %s" % (str(result))

            self._set_error_state(error)
            raise LoginError(error)

        # now save all of the needed data
        self._login_url = result["login_url"]
        self._identity_url = identity_url
        self._session_key = session_key
        self._signing_key = signing_key
        self._session_uid = session_uid
        self._status = _LoginStatus.LOGGING_IN

        qrcode = None

        if _has_qrcode():
            try:
                self._login_qrcode = _create_qrcode(self._login_url)
                qrcode = self._login_qrcode
            except:
                pass

        return (self._login_url,qrcode)

    def _poll_session_status(self):
        """Function used to query the identity service for this session
           to poll for the session status"""

        identity_url = self.identity_service_url()

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
            self._set_error_state(error)
            raise LoginError(error)

        # now update the status...
        status = result["session_status"]
        self._set_status(status)

    def wait_for_login(self, timeout=None, polling_delta=5):
        """Block until the user has logged in. If 'timeout' is set
           then we will wait for a maximum of that number of seconds

           This will check whether we have logged in by polling
           the identity service every 'polling_delta' seconds.
        """

        self._check_for_error()

        if not self.is_logging_in():
            return self.is_logged_in()

        polling_delta = int(polling_delta)
        if polling_delta > 60:
            polling_delta = 60
        elif polling_delta < 1:
            polling_delta = 1

        if timeout is None:
            # block forever....
            while True:
                self._poll_session_status()

                if self.is_logged_in():
                    return True

                elif not self.is_logging_in():
                    return False

                _time.sleep(polling_delta)
        else:
            # only block until the timeout has been reached
            timeout = int(timeout)
            if timeout < 1:
                timeout = 1

            start_time = _datetime.now()

            while (_datetime.now() - start_time).seconds < timeout:
                self._poll_session_status()

                if self.is_logged_in():
                    return True

                elif not self.is_logging_in():
                    return False

                _time.sleep(polling_delta)

            return False
