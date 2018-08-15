
import datetime as _datetime
import uuid as _uuid

import base64 as _base64

from ._function import string_to_bytes as _string_to_bytes
from ._function import bytes_to_string as _bytes_to_string

__all__ = [ "LoginSession" ]

class LoginSessionError(Exception):
    pass

class LoginSession:
    """This class holds all details of a single login session"""
    def __init__(self, public_key=None, public_cert=None, ip_addr=None,
                       hostname=None, login_message=None):
        self._pubkey = None
        self._uuid = None
        self._request_datetime = None
        self._login_datetime = None
        self._logout_datetime = None
        self._pubcert = None
        self._status = None
        self._ipaddr = None
        self._hostname = None
        self._login_message = None

        if public_key:
            try:
                public_key = open(public_key,"r").readlines()
            except:
                pass

            self._pubkey = public_key
            self._uuid = str(_uuid.uuid4())
            self._request_datetime = _datetime.datetime.utcnow()
            self._status = "unapproved"

        if public_cert:
            try:
                public_cert = open(public_cert,"r").readlines()
            except:
                pass

            self._pubcert = public_cert

        if ip_addr:
            self._ipaddr = ip_addr

        if hostname:
            self._hostname = hostname

        if login_message:
            self._login_message = login_message

    def public_key(self):
        """Return the public key"""
        if self._pubkey is None:
            raise LoginSessionError("You cannot get a public key from "
                     "a logged out or otherwise denied session")

        return self._pubkey

    def public_certificate(self):
        """Return the public certificate"""
       	if self._pubcert is None:
       	    raise LoginSessionError("You cannot	get a public key from "
       	       	     "a logged out or otherwise	denied session")

        return self._pubcert

    def request_source(self):
        """Return the IP address of the source of 
           this request. This is used to rate limit someone  
           who is maliciously requesting logins..."""
        return self._ipaddr

    def uuid(self):
        """Return the UUID of this request"""
        return self._uuid

    def short_uuid(self):
        """Return a short UUID that will be used to
           provide a more human-readable session ID"""
        if self._uuid:
            return self._uuid[:8]
        else:
            return None

    def regenerate_uuid(self):
        """Regenerate the UUID as there has been a clash"""
        if self._pubkey:
            self._uuid = str(_uuid.uuid4())

    def timestamp(self):
        """Return the timestamp of when this was created"""
        return self._request_datetime.timestamp()

    def creation_time(self):
        """Return the date and time when this was created"""
        return self._request_datetime

    def login_time(self):
        """Return the date and time when the user logged in. This
           returns None if the user has not yet logged in"""
        return self._login_datetime

    def logout_time(self):
        """Return the date and time when the user logged out. This
           returns None if the user has not yet logged out"""
        return self._logout_datetime

    def hours_since_creation(self):
        """Return the number of hours since this request was
           created. This will return a float, so 1 second is 
           1 / 3600th of an hour"""

        if self._datetime:
            delta = _datetime.datetime.utcnow() - self._datetime
            return delta.total_seconds() / 3600.0
        else:
            return 0

    def status(self):
        """Return the status of this login session"""
        return self._status

    def set_approved(self):
        """Register that this request has been approved"""
        if self._uuid:
            if self._pubkey is None or self._pubcert is None:
                raise LoginSessionError("You cannot approve a login session "
                    "that doesn't have a valid public key or certificate. "
                    "Perhaps you have already denied or logged out?")

            if self.status() != "unapproved":
                raise LoginSessionError("You cannot approve a login session "
                    "that is not in the 'unapproved' state. This login session "
                    "is in the '%s' state." % self.status())

            self._login_datetime = _datetime.datetime.utcnow()
            self._status = "approved"

    def _clear_keys_and_certs(self):
        """Function called to remove all keys and certificates
           from this session, as it has now been terminated
           (and so the keys and certs are no longer valid)
        """
        self._pubkey = None
        self._pubcert = None

    def set_denied(self):
        """Register that this request has been denied"""
        if self._uuid:
            self._status = "denied"
            self._clear_keys_and_certs()

    def set_logged_out(self):
        """Register that this request has been closed as 
           the user has logged out"""
        if self._uuid:
            self._status = "logged_out"
            self._logout_datetime = _datetime.datetime.utcnow()
            self._clear_keys_and_certs()

    def login(self):
        """Convenience function to set the session into the logged in state"""
        self.set_approved()

    def logout(self):
        """Convenience function to set the session into the logged out state"""
        self.set_logged_out()

    def is_approved(self):
        """Return whether or not this session is open and
           approved by the user"""
        if self._status:
            return self._status == "approved"
        else:
            return False

    def login_message(self):
        """Return any login message that has been set by the user"""
        return self._login_message

    def hostname(self):
        """Return the user-supplied hostname of the host making the
           login request"""
        return self._hostname

    def to_data(self):
        """Return a data version (dictionary) of this LoginSession"""

        if self._uuid is None:
            return None

        data = {}
        data["uuid"] = self._uuid
        data["timestamp"] = self._request_datetime.timestamp()

        try:
            data["login_timestamp"] = self._login_datetime.timestamp()
        except:
            data["login_timestamp"] = None

        try:
            data["logout_timestamp"] = self._logout_datetime.timestamp()
        except:
            data["logout_timestamp"] = None

        # the keys and certificate are arbitrary binary data.
        # These need to be base64 encoded and then turned into strings
        data["public_key"] = _bytes_to_string(self._pubkey)
        data["public_certificate"] = _bytes_to_string(self._pubcert)

        data["status"] = self._status
        data["ipaddr"] = self._ipaddr
        data["hostname"] = self._hostname
        data["login_message"] = self._login_message

        return data

    @staticmethod
    def from_data(data):
        """Return a LoginSession constructed from the passed data (dictionary)"""
        if data is None:
            return None

        try:
            logses = LoginSession()

            logses._uuid = data["uuid"]
            logses._request_datetime = _datetime.datetime \
                                        .fromtimestamp(float(data["timestamp"]))

            try:
                logses._login_datetime = _datetime.datetime \
                                           .fromtimestamp(float(data["login_timestamp"]))
            except:
                logses._login_datetime = None

            try:
                logses._logout_datetime = _datetime.datetime \
                                            .fromtimestamp(float(data["logout_timestamp"]))
            except:
                logses._logout_datetime = None

            # the keys and secret are arbitrary binary data.
            # These need to be base64 encoded and then turned into strings
            try:
                logses._pubkey = _string_to_bytes(data["public_key"])
            except:
                logses._pubkey = None

            try:
                logses._pubcert = _string_to_bytes(data["public_certificate"])
            except:
                logses._pubcert = None

            logses._status = data["status"]
            logses._ipaddr = data["ipaddr"]

            logses._hostname = data["hostname"]
            logses._login_message = data["login_message"]

            return logses

        except Exception as e:
            raise LoginSessionError("Cannot load the LoginSession from "
                      "the object store? error = %s" % (str(e)))
