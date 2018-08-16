
import uuid as _uuid

from ._keys import PrivateKey as _PrivateKey
from ._keys import PublicKey as _PublicKey
from ._otp import OTP as _OTP

from ._function import bytes_to_string as _bytes_to_string
from ._function import string_to_bytes as _string_to_bytes

__all__ = [ "Service" ]

class ServiceError(Exception):
    pass

class Service:
    """This class represents a service in the system. Services
       will either be identity services, access services or
       accounting services.
    """
    def __init__(self, service_type=None, service_url=None, admin_password=None):
        """Construct a new service of the specified type, with
           the specified URL."""
        self._service_type = service_type
        self._service_url = service_url

        if self._service_type:
            if not self._service_type in [ "identity", "access", "accounting" ]:
                raise ServiceError("Services of type '%s' are not allowed!" % \
                          self._service_type)

            self._uuid = str(_uuid.uuid4())
            self._privkey = _PrivateKey()
            self._pubkey = self._privkey.public_key()
            self._privcert = _PrivateKey()
            self._pubcert = self._privcert.public_key()

    def set_admin_password(self, password):
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

        self.verify_admin_user(password,otpcode)

        if password == new_password:
            return

        key = _PrivateKey.read_bytes(self._admin_password, password)
        otp = _OTP.decrypt(self._otc, key).verify(otpcode)

        newkey = _PrivateKey()
        self._admin_password = newkey.butes(new_password)
        self._otpsecret = otp.encrypt(new_key.public_key())

    def uuid(self):
        """Return the uuid of this service"""
        return self._uuid

    def service_type(self):
        """Return the type of this service"""
        return self._service_type

    def service_url(self):
        """Return the URL used to access this service"""
        return self._service_url

    def private_key(self):
        """Return the private key (if it has been unlocked)"""
        if self._privkey is None:
            raise ServiceError("The service '%s' has not been unlocked" % \
                               self._service_url)

        return self._privkey

    def private_certificate(self):
        """Return the private signing certificate (if it has been unlocked)"""
        if self._privcert is None:
            raise ServiceError("The service '%s' has not been unlocked" % \
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
        return self.private_certificate().sign(request)

    def verify(self, signature, message):
        """Verify that this service signed the message"""
        self.public_certificate().verify(signature, message)

    def encrypt(self, message):
        """Encrypt the passed message"""
        return self.public_key().encrypt(message)

    def decrypt(self, message):
        """Decrypt the passed message"""
        return self.private_key().decrypt(message)

    def verify_admin_user(self, password, otpcode):
        """Verify that we are the admin user verifying that
           the passed password and otpcode are correct. This does
           nothing if they are correct, but raises an exception
           if they are wrong"""

        try:
            key = _PrivateKey.read_bytes(self._admin_password, password)
        except Exception as e:
            raise ServiceError("Could not log into admin account: %s" % str(e))

        try:
            _OTP.decrypt(self._otc, key).verify(otpcode)
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
        data["public_certificate"] = _bytes_to_string(self._pubcert.bytes())
        data["public_key"] = _bytes_to_string(self._pubkey.bytes())

        if password:
            # only serialise private data if a password was provided
            data["private_certificate"] = _bytes_to_string(
                                         self._privcert.bytes(password))
            data["private_key"] = _bytes_to_string(
                                         self._privkey.bytes(password))
            data["otpsecret"] = _bytes_to_string( self._otp )
            data["admin_password"] = _bytes_to_string(self._admin_password)

    @staticmethod
    def from_data(data, password=None):
        """Deserialise this object from the passed data. This will 
           only deserialise the private key, private certificate, 
           and OTP if a valid password and passcode is supplied
        """

        Service service

        if password:
            # get the private info...
            service._privkey = _PrivateKey.read_bytes(
                                _string_to_bytes(data["private_key"],password))

            service._privcert = _PrivateKey.read_bytes(
                                _string_to_bytes(data["private_certificate"],password))

            service._otp = _string_to_bytes(data["otpsecret"])

            service._admin_password = _string_to_bytes(data["admin_password"])
        else:
            service._privkey = None
            service._privcert = None
            service._otp = None

        service._uuid = data["uuid"]
        service._service_type = data["service_type"]
        service._service_url = data["service_url"]

        service._pubkey = _PublicKey.read_bytes(
                                _string_to_bytes(data["public_key"]))
        service._pubcert = _PublicKey.read_bytes(
                                _string_to_bytes(data["public_certificate"]))

        return service
