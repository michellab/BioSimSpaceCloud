
import datetime as _datetime
import uuid as _uuid

import base64 as _base64

from Acquire.Crypto import PublicKey as _PublicKey

from ._errors import LoginSessionError

__all__ = ["LoginSession", "LoginSessionError"]


class LoginSession:
    """This class holds all details of a single login session"""
    def __init__(self, public_key=None, public_cert=None, ip_addr=None,
                 hostname=None, login_message=None):
        self._pubkey = None
        self._uid = None
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
                public_key = open(public_key, "r").readlines()
            except:
                pass

            try:
                self._pubkey = _PublicKey.from_data(public_key)
            except:
                self._pubkey = public_key

            if not isinstance(self._pubkey, _PublicKey):
                raise TypeError("The public key must be of type PublicKey")

            self._uid = str(_uuid.uuid4())
            self._request_datetime = _datetime.datetime.utcnow()
            self._status = "unapproved"

        if public_cert:
            try:
                public_cert = open(public_cert, "r").readlines()
            except:
                pass

            try:
                self._pubcert = _PublicKey.from_data(public_cert)
            except:
                self._pubcert = public_cert

            if not isinstance(self._pubcert, _PublicKey):
                raise TypeError("The public certificate must be of "
                                "type PublicKey")

        if ip_addr:
            self._ipaddr = ip_addr

        if hostname:
            self._hostname = hostname

        if login_message:
            self._login_message = login_message

    def __str__(self):
        if self.is_null():
            return "LoginSession::null"
        else:
            return "LoginSession(uid=%s, status=%s)" % \
                            (self.uid(), self.status())

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._uid == other._uid
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def is_null(self):
        """Return whether or not this object is null"""
        return self._uid is None

    def public_key(self):
        """Return the public key"""
        if self._pubkey is None:
            raise LoginSessionError(
                "You cannot get a public key from "
                "a logged out or otherwise denied session")

        elif self.is_suspicious():
            raise LoginSessionError(
                "You cannot get a public key from "
                "a login session that has been marked as suspicious")

        return self._pubkey

    def public_certificate(self):
        """Return the public certificate"""
        if self._pubcert is None:
            raise LoginSessionError(
               "You cannot get a public certificate from "
               "a logged out or otherwise denied session")

        elif self.is_suspicious():
            raise LoginSessionError(
                "You cannot get a public certificate from "
                "a login session that has been marked as suspicious")

        return self._pubcert

    def request_source(self):
        """Return the IP address of the source of
           this request. This is used to rate limit someone
           who is maliciously requesting logins..."""
        return self._ipaddr

    def uuid(self):
        """Return the UUID of this request"""
        return self._uid

    def short_uuid(self):
        """Return a short UUID that will be used to
           provide a more human-readable session ID"""
        if self._uid:
            return self._uid[:8]
        else:
            return None

    def uid(self):
        """Synonym for uuid"""
        return self.uuid()

    def short_uid(self):
        """Synonym for short_uuid"""
        return self.short_uuid()

    def regenerate_uuid(self):
        """Regenerate the UUID as there has been a clash"""
        if self._pubkey:
            self._uid = str(_uuid.uuid4())

    def regenerate_uid(self):
        """Synonym for regenerate_uuid"""
        self.regenerate_uuid()

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

        if self._request_datetime:
            delta = _datetime.datetime.utcnow() - self._request_datetime
            return delta.total_seconds() / 3600.0
        else:
            return 0

    def status(self):
        """Return the status of this login session"""
        return self._status

    def set_suspicious(self):
        """Put this login session into a suspicious state. This
           will be because weird activity has been detected which indicates
           that the session may be have been cracked. A login session
           in a suspicious state should not be granted any permissions.
        """
        if self._uid:
            self._status = "suspicious"

    def set_approved(self):
        """Register that this request has been approved"""
        if self._uid:
            if self._pubkey is None or self._pubcert is None:
                raise LoginSessionError(
                    "You cannot approve a login session "
                    "that doesn't have a valid public key or certificate. "
                    "Perhaps you have already denied or logged out?")

            if self.status() != "unapproved":
                raise LoginSessionError(
                    "You cannot approve a login session "
                    "that is not in the 'unapproved' state. This login "
                    "session is in the '%s' state." % self.status())

            self._login_datetime = _datetime.datetime.utcnow()
            self._status = "approved"

    def _clear_keys(self):
        """Function called to remove all keys
           from this session, as it has now been terminated
           (and so the keys are no longer valid)
        """
        self._pubkey = None

    def set_denied(self):
        """Register that this request has been denied"""
        if self._uid:
            self._status = "denied"
            self._clear_keys()
            # also clear the certificate
            self._pubcert = None

    def set_logged_out(self):
        """Register that this request has been closed as
           the user has logged out"""
        if self._uid:
            self._status = "logged_out"
            self._logout_datetime = _datetime.datetime.utcnow()
            self._clear_keys()

    def login(self):
        """Convenience function to set the session into the logged in state"""
        self.set_approved()

    def logout(self):
        """Convenience function to set the session into the logged out state"""
        self.set_logged_out()

    def is_suspicious(self):
        """Return whether or not this session is suspicious"""
        if self._status:
            return self._status == "suspicious"
        else:
            return False

    def is_approved(self):
        """Return whether or not this session is open and
           approved by the user"""
        if self._status:
            return self._status == "approved"
        else:
            return False

    def is_logged_out(self):
        """Return whether or not this session has logged out"""
        if self._status:
            return self._status == "logged_out"
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

        if self._uid is None:
            return None

        data = {}
        data["uid"] = self._uid
        data["timestamp"] = self._request_datetime.timestamp()

        try:
            data["login_timestamp"] = self._login_datetime.timestamp()
        except:
            data["login_timestamp"] = None

        try:
            data["logout_timestamp"] = self._logout_datetime.timestamp()
        except:
            data["logout_timestamp"] = None

        if self._pubkey:
            data["public_key"] = self._pubkey.to_data()

        if self._pubcert:
            data["public_certificate"] = self._pubcert.to_data()

        data["status"] = self._status
        data["ipaddr"] = self._ipaddr
        data["hostname"] = self._hostname
        data["login_message"] = self._login_message

        return data

    @staticmethod
    def from_data(data):
        """Return a LoginSession constructed from the passed data
           (dictionary)
        """
        if data is None:
            return None

        try:
            logses = LoginSession()

            try:
                logses._uid = data["uid"]
            except:
                logses._uid = data["uuid"]  # for backward compatibility

            logses._request_datetime = _datetime.datetime\
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

            try:
                logses._pubkey = _PublicKey.from_data(data["public_key"])
            except:
                logses._pubkey = None

            try:
                logses._pubcert = _PublicKey.from_data(
                                            data["public_certificate"])
            except:
                logses._pubcert = None

            logses._status = data["status"]
            logses._ipaddr = data["ipaddr"]

            logses._hostname = data["hostname"]
            logses._login_message = data["login_message"]

            return logses

        except Exception as e:
            raise LoginSessionError(
                "Cannot load the LoginSession from "
                "the object store? error = %s" % (str(e)))
