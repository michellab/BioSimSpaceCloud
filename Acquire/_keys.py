
import os as _os
import tempfile as _tempfile
import re as _re

from cryptography.hazmat.primitives.asymmetric import rsa as _rsa
from cryptography.hazmat.primitives import serialization as _serialization
from cryptography.hazmat.backends import default_backend as _default_backend
from cryptography.hazmat.primitives import hashes as _hashes
from cryptography.hazmat.primitives.asymmetric import padding as _padding

__all__ = ["Keys", "PrivateKey", "PublicKey"]

class WeakPassphraseError(Exception):
    pass

class KeyManipulationError(Exception):
    pass

class SignatureVerificationError(Exception):
    pass

def _assert_strong_passphrase(passphrase, mangleFunction):
    """This function returns whether or not the passed  
       passphrase is sufficiently strong. To be strong,
       the password must be between 6-12 characters,
       mix upper and lower case, and contain letters and
       numbers
    """

    if mangleFunction:
        passphrase = str( mangleFunction(passphrase) )
    else:
        passphrase = str(passphrase)

    if len(passphrase) < 6 or len(passphrase) > 12:
        raise WeakPassphraseError("The pass-phrase must contain between "
                                  "6 and 12 characters")

    if not (_re.search(r'[A-Z]', passphrase) and
            _re.search(r'[a-z]', passphrase) and
            _re.search(r'[0-9]', passphrase)):
        raise WeakPassphraseError("The pass-phrase must contain numbers and "
                                  "upper- and lowercase characters")

    return passphrase

def _generate_private_key():
    """Internal function that is used to generate all of our private keys"""
    return _rsa.generate_private_key(
                    public_exponent=65537,
                    key_size=2048,
                    backend=_default_backend())        

class PublicKey:
    """This is a holder for an in-memory public key"""
    def __init__(self, public_key=None):
        """Construct from the passed public key"""
        self._pubkey = public_key

    def write(self, filename):
        """Write this public key to 'filename'"""
        pubkey_bytes = self._pubkey.public_bytes(
                            encoding=_serialization.Encoding.PEM,
                            format=_serialization.PublicFormat.SubjectPublicKeyInfo)

        with open(filename, "wb") as FILE:
            FILE.write(pubkey_bytes)           

    @staticmethod
    def read(filename):
        """Read and return a public key from 'filename'"""
        with open(filename, "rb") as FILE:
            public_key = _serialization.load_pem_public_key(
                            FILE.read(), backend=_default_backend())

            return PublicKey(public_key)

    def verify(self, signature, message):
        """Verify that the message has been correctly signed"""
        if self._pubkey is None:
            raise KeyManipulationError( "You cannot verify a message using "
                                        "an empty public key!" )

        try:
            self._pubkey.verify(
                          signature,
                          message,
                          _padding.PSS(
                             mgf=_padding.MGF1(_hashes.SHA256()),
                             salt_length=_padding.PSS.MAX_LENGTH),
                          _hashes.SHA256() )
        except Exception as e:
            raise SignatureVerificationError( "Error validating the signature "
                       "for the passed message: %s" % str(e) )

class PrivateKey:
    """This is a holder for an in-memory private key"""
    def __init__(self, private_key=None):
        """Construct the key either from a passed key, or by generating
           a new key"""
        if not private_key:
            self._privkey = _generate_private_key()
        else:
            self._privkey = private_key

    @staticmethod
    def read(filename, passphrase, mangleFunction=None):
        """Read a private key from 'filename' that is encrypted using
           'passphrase' and return a PrivateKey object holding that 
           key"""

        passphrase = _assert_strong_passphrase(passphrase, mangleFunction)

        private_key = None

        try:
            with open(filename, "rb") as FILE:
                private_key = _serialization.load_pem_private_key(
                                 FILE.read(),
                                 password=passphrase.encode("utf-8"),
                                 backend=_default_backend())
        except IOError as e:
            raise KeyManipulationError( "Cannot read the private keyfile %s: %s" % \
                                         (keyfile,str(e)) )
        except Exception as e:
            raise KeyManipulationError( "Cannot unlock key %s. Invalid Password?" % \
                                         (keyfile) )

        return PrivateKey(private_key)

    def write(self, filename, passphrase, mangleFunction=None):
        """Write this key to 'filename', encrypted with 'passphrase'"""

        if self._privkey is None:
            return

        passphrase = _assert_strong_passphrase(passphrase)

        # now write the key to disk, encrypted using the
        # supplied passphrase
        privkey_bytes = self._privkey.private_bytes(
                            encoding=_serialization.Encoding.PEM,
                            format=_serialization.PrivateFormat.PKCS8,
                            encryption_algorithm=_serialization.BestAvailableEncryption(
                                                     passphrase.encode("utf-8")))

        with open(_os.open(filename,
                  _os.O_CREAT | _os.O_WRONLY, 0o700), 'wb') as FILE:
            FILE.write(privkey_bytes)

    def public_key(self, filename=None):
        """Get the public key for this private key. If filename is
           specified then this is written to the passed file"""

        if self._privkey is None:
            return None

        return PublicKey(self._privkey.public_key())

    def sign(self, message):
        """Return the signature for the passed message"""
        if self._privkey is None:
            return None

        signature = self._privkey.sign(
                     message,
                     _padding.PSS(
                       mgf=_padding.MGF1(_hashes.SHA256()),
                       salt_length=_padding.PSS.MAX_LENGTH),
                     _hashes.SHA256() )

        return signature

class Keys:
    @staticmethod
    def assert_valid_passphrase(keyfile, passphrase, mangleFunction=None):
        """This function asserts that the supplied passphrase
           will unlock the passed user_account"""

        passphrase = _assert_strong_passphrase(passphrase, mangleFunction)

        try:
            with open(keyfile, "rb") as FILE:
                private_key = _serialization.load_pem_private_key(
                                 FILE.read(),
                                 password=passphrase.encode("utf-8"),
                                 backend=_default_backend())
        except IOError as e:
            raise KeyManipulationError( "Cannot read the private keyfile %s: %s" % \
                                         (keyfile,str(e)) )
        except Exception as e:
            raise KeyManipulationError( "Cannot unlock key %s. Invalid Password?" % \
                                         (keyfile) )

    @staticmethod
    def create_key_pair(passphrase, mangleFunction=None):
        """Create a public/private key pair, with the private
           key encrypted using the passed passphrase"""

        passphrase = _assert_strong_passphrase(passphrase, mangleFunction)

        # create a directory to hold all of the keys
        tmpdir = _tempfile.mkdtemp()

        privkey = "%s/credentials.pem" % tmpdir
        pubkey = "%s/credentials_public.pem" % tmpdir

        # use pyca cryptography to generate the private key
        private_key = _generate_private_key()

        # now write the key to disk, encrypted using the
        # supplied passphrase
        privkey_bytes = private_key.private_bytes(
                            encoding=_serialization.Encoding.PEM,
                            format=_serialization.PrivateFormat.PKCS8,
                            encryption_algorithm=_serialization.BestAvailableEncryption(
                                                     passphrase.encode("utf-8")))

        with open(_os.open(privkey,
                  _os.O_CREAT | _os.O_WRONLY, 0o700), 'wb') as FILE:
            FILE.write(privkey_bytes)

        # now generate the public key
        public_key = private_key.public_key()
        pubkey_bytes = public_key.public_bytes(
                            encoding=_serialization.Encoding.PEM,
                            format=_serialization.PublicFormat.SubjectPublicKeyInfo)

        with open(pubkey, "wb") as FILE:
            FILE.write(pubkey_bytes)

        return (privkey, pubkey)

