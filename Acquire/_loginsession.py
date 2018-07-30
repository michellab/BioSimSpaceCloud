
import datetime as _datetime
import uuid as _uuid

__all__ = [ "LoginSession" ]

class LoginSession:
    """This class holds all details of a single login session"""
    def __init__(self, public_key=None, public_cert=None, ip_addr=None):
        self._pubkey = None
        self._uuid = None
        self._datetime = None
        self._pubcert = None
        self._status = None
        self._ipaddr = None

        if public_key:
            try:
                public_key = open(public_key,"r").readlines()
            except:
                pass

            self._pubkey = public_key
            self._uuid = str(_uuid.uuid4())
            self._datetime = _datetime.datetime.utcnow()
            self._status = "unapproved"

        if public_cert:
            try:
                public_cert = open(public_cert,"r").readlines()
            except:
                pass

            self._pubcert = public_cert

        if ip_addr:
            self._ipaddr = ip_addr

    def public_key(self):
        """Return the public key"""
        return self._pubkey

    def public_certificate(self):
        """Return the public certificate"""
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
        return self._datetime.timestamp()

    def creation_time(self):
        """Return the date and time when this was created"""
        return self._datetime

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
            self._status = "approved"

    def set_denied(self):
        """Register that this request has been denied"""
        if self._uuid:
            self._status = "denied"

    def set_logged_out(self):
        """Register that this request has been closed as 
           the user has logged out"""
        if self._uuid:
            self._status = "logged_out"

    def is_approved(self):
        """Return whether or not this session is open and
           approved by the user"""
        if self._status:
            return self._status == "approved"
        else:
            return False

    def to_data(self):
        """Return a data version (dictionary) of this LoginSession"""

        if self._uuid is None:
            return None

        data = {}
        data["uuid"] = self._uuid
        data["timestamp"] = self._datetime.timestamp()
        data["public_key"] = self._pubkey
        data["public_certificate"] = self._pubcert
        data["status"] = self._status
        data["ipaddr"] = self._ipaddr

        return data

    @staticmethod
    def from_data(data):
        """Return a LoginSession constructed from the passed data (dictionary)"""
        if data is None:
            return None

        logses = LoginSession()

        logses._uuid = data["uuid"]
        logses._datetime = _datetime.datetime \
                                    .fromtimestamp(float(data["timestamp"]))
        logses._pubkey = data["public_key"]
        logses._pubcert = data["public_certificate"]

        logses._status = data["status"]
        logses._ipaddr = data["ipaddr"]

        return logses
