
import os as _os
import base64 as _base64

import lazy_import as _lazy_import

from ._errors import WeakPassphraseError, KeyManipulationError, \
                     SignatureVerificationError
from ._errors import DecryptionError

# tempfile = _lazy_import.lazy_module("tempfile")
import tempfile as _tempfile

_pyotp = _lazy_import.lazy_module("pyotp")

_re = _lazy_import.lazy_module("re")

_rsa = _lazy_import.lazy_module(
            "cryptography.hazmat.primitives.asymmetric.rsa")
_serialization = _lazy_import.lazy_module(
            "cryptography.hazmat.primitives.serialization")
_default_backend = _lazy_import.lazy_function(
            "cryptography.hazmat.backends.default_backend")
_hashes = _lazy_import.lazy_module("cryptography.hazmat.primitives.hashes")
_padding = _lazy_import.lazy_module(
            "cryptography.hazmat.primitives.asymmetric.padding")
_fernet = _lazy_import.lazy_module("cryptography.fernet")

__all__ = ["PrivateKey", "PublicKey"]


def _bytes_to_string(b):
    """Return the passed binary bytes safely encoded to
       a base64 utf-8 string"""
    if b is None:
        return None
    else:
        return _base64.b64encode(b).decode("utf-8")


def _string_to_bytes(s):
    """Return the passed base64 utf-8 encoded binary data
       back converted from a string back to bytes. Note that
       this can only convert strings that were encoded using
       bytes_to_string - you cannot use this to convert
       arbitrary strings to bytes"""
    if s is None:
        return None
    else:
        return _base64.b64decode(s.encode("utf-8"))


def _assert_strong_passphrase(passphrase, mangleFunction):
    """This function returns whether or not the passed
       passphrase is sufficiently strong. To be strong,
       the password must be between 6-20 characters,
       mix upper and lower case, and contain letters and
       numbers
    """

    if mangleFunction:
        passphrase = str(mangleFunction(passphrase))
    else:
        passphrase = str(passphrase)

    if len(passphrase) < 6 or len(passphrase) > 20:
        raise WeakPassphraseError("The pass-phrase '%s' must contain between "
                                  "6 and 20 characters" % passphrase)

    if not (_re.search(r'[A-Z]', passphrase) and
            _re.search(r'[a-z]', passphrase) and
            _re.search(r'[0-9]', passphrase)):
        raise WeakPassphraseError("The pass-phrase must contain numbers and "
                                  "upper- and lowercase characters")

    return passphrase


def _generate_private_key():
    """Internal function that is used to generate all of our private keys"""
    return _rsa.generate_private_key(public_exponent=65537,
                                     key_size=2048,
                                     backend=_default_backend())


class PublicKey:
    """This is a holder for an in-memory public key"""
    def __init__(self, public_key=None):
        """Construct from the passed public key"""
        self._pubkey = public_key

    def bytes(self):
        """Return the raw bytes for this key"""
        if self._pubkey is None:
            return None

        return self._pubkey.public_bytes(
            encoding=_serialization.Encoding.PEM,
            format=_serialization.PublicFormat
                                 .SubjectPublicKeyInfo)

    def __str__(self):
        """Return a string representation of this key"""
        return "PublicKey('%s')" % self.bytes().decode("utf-8")

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.bytes() == other.bytes()
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def write(self, filename):
        """Write this public key to 'filename'"""
        if self._pubkey is None:
            return

        pubkey_bytes = self.bytes()

        with open(filename, "wb") as FILE:
            FILE.write(pubkey_bytes)

    @staticmethod
    def read_bytes(data):
        """Read and return a public key from 'data'"""
        public_key = _serialization.load_pem_public_key(
                        data, backend=_default_backend())

        return PublicKey(public_key)

    @staticmethod
    def read(filename):
        """Read and return a public key from 'filename'"""
        with open(filename, "rb") as FILE:
            return PublicKey.read_bytes(FILE.read())

    def encrypt(self, message):
        """Encrypt and return the passed message. For short messages this
           will use the private key directly. For longer messages,
           this will generate a random
           symmetric key, will encrypt the message using that, and will then
           encrypt the symmetric key. This returns some bytes
        """
        if isinstance(message, str):
            message = message.encode("utf-8")

        try:
            return self._pubkey.encrypt(
                        message,
                        _padding.OAEP(
                            mgf=_padding.MGF1(algorithm=_hashes.SHA256()),
                            algorithm=_hashes.SHA256(),
                            label=None)
                        )
        except:
            pass

        # this is a longer message that cannot be encoded using
        # an asymmetric key - need to use a symmetric key
        key = _fernet.Fernet.generate_key()
        f = _fernet.Fernet(key)
        token = f.encrypt(message)

        encrypted_key = self._pubkey.encrypt(
                            key,
                            _padding.OAEP(
                                mgf=_padding.MGF1(algorithm=_hashes.SHA256()),
                                algorithm=_hashes.SHA256(),
                                label=None)
                            )

        # the first 256 bytes are the encrypted key - the rest
        # is the token, because we are using 2048 bit (256 byte) keys
        return encrypted_key + token

    def verify(self, signature, message):
        """Verify that the message has been correctly signed"""
        if self._pubkey is None:
            raise KeyManipulationError("You cannot verify a message using "
                                       "an empty public key!")

        if isinstance(message, str):
            message = message.encode("utf-8")

        try:
            self._pubkey.verify(
                          signature,
                          message,
                          _padding.PSS(
                             mgf=_padding.MGF1(_hashes.SHA256()),
                             salt_length=_padding.PSS.MAX_LENGTH),
                          _hashes.SHA256())
        except Exception as e:
            raise SignatureVerificationError(
                       "Error validating the signature "
                       "for the passed message: %s" % str(e))

    def to_data(self):
        """Return this public key as a json-serialisable dictionary"""
        data = {}

        b = self.bytes()

        if b is not None:
            data["bytes"] = _bytes_to_string(self.bytes())

        return data

    @staticmethod
    def from_data(data):
        """Construct from the passed json-deserialised dictionary"""
        if isinstance(data, str):
            return PublicKey.read_bytes(_string_to_bytes(data))

        elif isinstance(data, bytes):
            return PublicKey.read_bytes(data)

        else:
            key = PublicKey()

            if (data and len(data) > 0):
                key = PublicKey.read_bytes(_string_to_bytes(data["bytes"]))

            return key


class PrivateKey:
    """This is a holder for an in-memory private key"""
    def __init__(self, private_key=None):
        """Construct the key either from a passed key, or by generating
           a new key"""
        if not private_key:
            self._privkey = _generate_private_key()
        else:
            self._privkey = private_key

    def __str__(self):
        """Return a string representation of this key"""
        return "PrivateKey( public_key='%s' )" % \
            self.public_key().bytes().decode("utf-8")

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.public_key() == other.public_key()
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    @staticmethod
    def read_bytes(data, passphrase, mangleFunction=None):
        """Read a private key from the passed bytes 'data' that
           is encrypted using 'passphrase' and return a PrivateKey
           object holding that key
        """

        passphrase = _assert_strong_passphrase(passphrase, mangleFunction)

        private_key = None

        try:
            private_key = _serialization.load_pem_private_key(
                             data,
                             password=passphrase.encode("utf-8"),
                             backend=_default_backend())
        except Exception as e:
            raise KeyManipulationError("Cannot unlock key. %s" %
                                       str(e))

        return PrivateKey(private_key)

    @staticmethod
    def read(filename, passphrase, mangleFunction=None):
        """Read a private key from 'filename' that is encrypted using
           'passphrase' and return a PrivateKey object holding that
           key"""

        data = None

        try:
            with open(filename, "rb") as FILE:
                data = FILE.read()
        except IOError as e:
            raise KeyManipulationError(
                    "Cannot read the private keyfile %s: %s" %
                    (filename, str(e)))

        return PrivateKey.read_bytes(data, passphrase, mangleFunction)

    def bytes(self, passphrase, mangleFunction=None):
        """Return the raw bytes for this key, encoded by the passed
           passphrase that has been optionally mangled by mangleFunction"""
        if self._privkey is None:
            return None

        passphrase = _assert_strong_passphrase(passphrase, mangleFunction)

        return self._privkey.private_bytes(
                encoding=_serialization.Encoding.PEM,
                format=_serialization.PrivateFormat.PKCS8,
                encryption_algorithm=_serialization.BestAvailableEncryption(
                                        passphrase.encode("utf-8")))

    def write(self, filename, passphrase, mangleFunction=None):
        """Write this key to 'filename', encrypted with 'passphrase'"""

        if self._privkey is None:
            return

        privkey_bytes = self.bytes(passphrase, mangleFunction)

        with open(_os.open(filename,
                  _os.O_CREAT | _os.O_WRONLY, 0o700), 'wb') as FILE:
            FILE.write(privkey_bytes)

    def public_key(self, filename=None):
        """Get the public key for this private key. If filename is
           specified then this is written to the passed file"""

        if self._privkey is None:
            return None

        return PublicKey(self._privkey.public_key())

    def key_size_in_bytes(self):
        """Return the number of bytes in this key"""
        if self._privkey is None:
            return 0
        else:
            return int(self._privkey.key_size / 8)

    def encrypt(self, message):
        """Encrypt and return the passed message"""
        return self.public_key().encrypt(message)

    def verify(self, signature, message):
        """Verify the passed signature is correct for the passed message"""
        return self.public_key().verify(signature, message)

    def decrypt(self, message):
        """Decrypt and return the passed message"""
        key_size = self.key_size_in_bytes()

        if key_size == 0:
            raise DecryptionError("You cannot decrypt a message "
                                  "with a null key!")

        # try standard decryption
        try:
            return self._privkey.decrypt(
                message,
                _padding.OAEP(
                    mgf=_padding.MGF1(algorithm=_hashes.SHA256()),
                    algorithm=_hashes.SHA256(),
                    label=None))
        except:
            pass

        # it is a larger message, so need to decrypt the secret symmetric
        # key, and then use that to decrypt the rest of the token
        try:
            symkey = self._privkey.decrypt(
                        message[0:key_size],
                        _padding.OAEP(
                            mgf=_padding.MGF1(algorithm=_hashes.SHA256()),
                            algorithm=_hashes.SHA256(),
                            label=None))
        except Exception as e:
            raise DecryptionError(
                "Cannot decrypt the symmetric key used "
                "to encrypt the long message '%s' (%s): %s" %
                (message[0:key_size], key_size, str(e)))

        try:
            f = _fernet.Fernet(symkey)
        except:
            f = _fernet.Fernet(symkey.decode("utf-8"))

        try:
            try:
                return f.decrypt(message[key_size:])
            except:
                return f.decrypt(message[key_size:].encode("utf-8"))
        except Exception as e:
            raise DecryptionError(
                    "Cannot decrypt the long message using the "
                    "symmetric key: %s" % str(e))

    def sign(self, message):
        """Return the signature for the passed message"""
        if self._privkey is None:
            return None

        if isinstance(message, str):
            message = message.encode("utf-8")

        signature = self._privkey.sign(
                     message,
                     _padding.PSS(
                       mgf=_padding.MGF1(_hashes.SHA256()),
                       salt_length=_padding.PSS.MAX_LENGTH),
                     _hashes.SHA256())

        return signature

    def to_data(self, passphrase, mangleFunction=None):
        """Return the json-serialisable data for this key"""
        data = {}

        b = self.bytes(passphrase, mangleFunction)

        if b is not None:
            data["bytes"] = _bytes_to_string(b)

        return data

    @staticmethod
    def from_data(data, passphrase, mangleFunction=None):
        """Return a private key constructed from the passed json-deserialised
           dictionary
        """

        if isinstance(data, str):
            return PrivateKey.read_bytes(_string_to_bytes(data),
                                         passphrase, mangleFunction)

        elif isinstance(data, bytes):
            return PrivateKey.read_bytes(data, passphrase, mangleFunction)

        else:
            key = PrivateKey()

            if (data and len(data) > 0):
                key = PrivateKey.read_bytes(_string_to_bytes(data["bytes"]),
                                            passphrase, mangleFunction)

            return key
