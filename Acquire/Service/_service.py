
import uuid as _uuid
from copy import copy as _copy

from Acquire.Crypto import PrivateKey as _PrivateKey
from Acquire.Crypto import PublicKey as _PublicKey
from Acquire.Crypto import OTP as _OTP

from Acquire.ObjectStore import bytes_to_string as _bytes_to_string
from Acquire.ObjectStore import string_to_bytes as _string_to_bytes

__all__ = ["Service"]


class ServiceError(Exception):
    pass


class Service:
    """This class represents a service in the system. Services
       will either be identity services, access services or
       accounting services.
    """
    def __init__(self, service_type=None, service_url=None):
        """Construct a new service of the specified type, with
           the specified URL."""
        self._service_type = service_type
        self._service_url = service_url

        if self._service_type:
            if self._service_type not in ["identity", "access", "accounting"]:
                raise ServiceError("Services of type '%s' are not allowed!" %
                                   self._service_type)

            self._uuid = str(_uuid.uuid4())
            self._privkey = _PrivateKey()
            self._pubkey = self._privkey.public_key()
            self._privcert = _PrivateKey()
            self._pubcert = self._privcert.public_key()
            self._admin_password = None

    def set_admin_password(self, admin_password):
        """Set the admin password for this service. This returns the
           provisioning URI for the OTP shared secret"""
        if self._admin_password:
            raise ServiceError("The admin password has already been set!")

        key = _PrivateKey()
        self._admin_password = key.bytes(admin_password)
        otp = _OTP()
        self._otpsecret = otp.encrypt(key.public_key())
        return otp.provisioning_uri("admin", self.service_url())

    def reset_admin_password(self, password, otpcode, new_password):
        """Change the admin password for this service. Note that
           you must pass in a valid password and otpcode to make the change"""

        self.verify_admin_user(password, otpcode)

        if password == new_password:
            return

        key = _PrivateKey.read_bytes(self._admin_password, password)
        otp = _OTP.decrypt(self._otpsecret, key)
        otp.verify(otpcode)

        newkey = _PrivateKey()
        self._admin_password = newkey.bytes(new_password)
        self._otpsecret = otp.encrypt(newkey.public_key())

    def uuid(self):
        """Return the uuid of this service"""
        return self._uuid

    def uid(self):
        """Synonym for uuid"""
        return self.uuid()

    def service_type(self):
        """Return the type of this service"""
        return self._service_type

    def is_identity_service(self):
        """Return whether or not this is an identity service"""
        if self._service_type:
            return self._service_type == "identity"
        else:
            return False

    def is_access_service(self):
        """Return whether or not this is an access service"""
        if self._service_type:
            return self._service_type == "access"
        else:
            return False

    def is_accounting_service(self):
        """Return whether or not this is an accounting service"""
        if self._service_type:
            return self._service_type == "accounting"
        else:
            return False

    def service_url(self):
        """Return the URL used to access this service"""
        return self._service_url

    def canonical_url(self):
        """Return the canonical URL for this service (this is the URL the
           service thinks it has, and which it has used to register itself
           with all other services)
        """
        return self._canonical_url

    def update_service_url(self, service_url):
        """Update the service url to be 'service_url'"""
        self._service_url = str(service_url)

    def private_key(self):
        """Return the private key (if it has been unlocked)"""
        if self._privkey is None:
            raise ServiceError("The service '%s' has not been unlocked" %
                               self._service_url)

        return self._privkey

    def private_certificate(self):
        """Return the private signing certificate (if it has been unlocked)"""
        if self._privcert is None:
            raise ServiceError("The service '%s' has not been unlocked" %
                               self._service_url)

        return self._privcert

    def public_key(self):
        """Return the public key for this service"""
        return self._pubkey

    def public_certificate(self):
        """Return the public signing certificate for this service"""
        return self._pubcert

    def sign(self, message):
        """Sign the specified message"""
        return self.private_certificate().sign(message)

    def verify(self, signature, message):
        """Verify that this service signed the message"""
        self.public_certificate().verify(signature, message)

    def encrypt(self, message):
        """Encrypt the passed message"""
        return self.public_key().encrypt(message)

    def decrypt(self, message):
        """Decrypt the passed message"""
        return self.private_key().decrypt(message)

    def verify_admin_user(self, password, otpcode, remember_device=False):
        """Verify that we are the admin user verifying that
           the passed password and otpcode are correct. This does
           nothing if they are correct, but raises an exception
           if they are wrong. If 'remember_device' this this returns
           the provisioning_uri for the OTP generator"""

        try:
            key = _PrivateKey.read_bytes(self._admin_password, password)
        except Exception as e:
            raise ServiceError("Could not log into admin account: %s" % str(e))

        try:
            otp = _OTP.decrypt(self._otpsecret, key)
            otp.verify(otpcode)
            if remember_device:
                return otp.provisioning_uri("admin", self.service_url())
        except Exception as e:
            raise ServiceError("Could not log into admin account: %s" % str(e))

    def to_data(self, password=None):
        """Serialise this key to a dictionary, using the supplied
           password to encrypt the private key and certificate"""

        data = {}

        data["uuid"] = self._uuid
        data["service_type"] = self._service_type
        data["service_url"] = self._service_url

        # keys are binary and need to be encoded
        data["public_certificate"] = self._pubcert.to_data()
        data["public_key"] = self._pubkey.to_data()

        if password:
            # only serialise private data if a password was provided
            data["private_certificate"] = self._privcert.to_data(password)
            data["private_key"] = self._privkey.to_data(password)
            data["otpsecret"] = _bytes_to_string(self._otpsecret)
            data["admin_password"] = _bytes_to_string(self._admin_password)

        return data

    @staticmethod
    def from_data(data, password=None):
        """Deserialise this object from the passed data. This will
           only deserialise the private key, private certificate,
           and OTP if a valid password and passcode is supplied
        """

        service = Service()

        if password:
            # get the private info...
            service._privkey = _PrivateKey.from_data(data["private_key"],
                                                     password)

            service._privcert = _PrivateKey.from_data(
                                                data["private_certificate"],
                                                password)

            service._otpsecret = _string_to_bytes(data["otpsecret"])

            service._admin_password = _string_to_bytes(data["admin_password"])
        else:
            service._privkey = None
            service._privcert = None
            service._otpsecret = None

        service._uuid = data["uuid"]
        service._service_type = data["service_type"]
        service._service_url = data["service_url"]
        service._canonical_url = service._service_url

        service._pubkey = _PublicKey.from_data(data["public_key"])
        service._pubcert = _PublicKey.from_data(data["public_certificate"])

        if service.is_identity_service():
            from Acquire.Identity import IdentityService as _IdentityService
            return _IdentityService(service)
        elif service.is_access_service():
            from Acquire.Access import AccessService as _AccessService
            return _AccessService(service)
        elif service.is_accounting_service():
            from Acquire.Accounting import AccountingService \
                                        as _AccountingService
            return _AccountingService(service)
        else:
            return service
