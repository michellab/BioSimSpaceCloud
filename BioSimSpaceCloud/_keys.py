
import os as _os
import tempfile as _tempfile
import re as _re

__all__ = ["Keys"]

class WeakPassphraseError(Exception):
    pass

class KeyManipulationError(Exception):
    pass

class Keys:
    @staticmethod
    def assert_strong_passphrase(passphrase):
        """This function returns whether or not the passed 
           passphrase is sufficiently strong. To be strong,
           the password must be between 6-12 characters,
           mix upper and lower case, and contain letters and
           numbers
        """

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

    @staticmethod
    def assert_valid_passphrase(keyfile, passphrase, mangleFunction=None):
        """This function asserts that the supplied passphrase
           will unlock the passed user_account"""

        passphrase = Keys.assert_strong_passphrase(passphrase)

        if mangleFunction:
            passphrase = mangleFunction(passphrase)

        # create a directory to hold all of the keys
        tmpdir = _tempfile.mkdtemp()

        passphrase_file = "%s/passphrase" % tmpdir
        privkey = "%s/credentials.pem" % tmpdir
        pubkey = "%s/credentials_public.pem" % tmpdir

        # now turn the keyfile into lines
        try:
            privkey_lines = open(keyfile,"r").readlines()
        except:
            privkey_lines = keyfile

        # create a file readable only by this user in the passphrase
        # can be written. Need to do this as passing the passphrase 
        # via a command line argument is not secure - anyone can see it!
        with open(_os.open(passphrase_file, 
                           _os.O_CREAT | _os.O_WRONLY, 0o700), 'w') as FILE:
            FILE.write(passphrase)

        try:
            # now write the account's private key to a file (user readable only)
            with open(_os.open(privkey,
                      _os.O_CREAT | _os.O_WRONLY, 0o700), 'w') as FILE:
                for line in privkey_lines:
                    FILE.write(line)

            # now generate the public key
            cmd = "openssl rsa -pubout -in %s -out %s -passin file:%s" % \
                       (privkey,pubkey,passphrase_file)

            status = _os.system(cmd)

            if status != 0:
                raise KeyManipulationError("Cannot unlock the public key "
                                           "using the passed passphrase! "
                                           "Invalid password: %s" % status)

        finally:
            # remove any keys that have been generated
            try:
                _os.remove(passphrase_file)
                _os.remove(privkey)
                _os.remove(pubkey)
                _os.rmdir(tmpdir)
            except:
                pass

    @staticmethod
    def create_key_pair(passphrase, mangleFunction=None):
        """Create a public/private key pair, with the private
           key encrypted using the passed passphrase"""

        passphrase = Keys.assert_strong_passphrase(passphrase)

        if mangleFunction:
            passphrase = mangleFunction(passphrase)

        # create a directory to hold all of the keys
        tmpdir = _tempfile.mkdtemp()

        passphrase_file = "%s/passphrase" % tmpdir
        privkey = "%s/credentials.pem" % tmpdir
        pubkey = "%s/credentials_public.pem" % tmpdir

        # create a file readable only by this user in the passphrase
        # can be written. Need to do this as passing the passphrase 
        # via a command line argument is not secure - anyone can see it!
        with open(_os.open(passphrase_file, 
                           _os.O_CREAT | _os.O_WRONLY, 0o700), 'w') as FILE:
            FILE.write(passphrase)

        try:
            # Use openssl to generate the private key
            cmd = "openssl genrsa -out %s -aes128 -passout file:%s 2048" % \
                      (privkey,passphrase_file)

            status = _os.system(cmd)

            if status != 0:
                raise KeyManipulationError(
                       "Cannot create the private key (%s)!" % privkey)

            # ensure that only we can read the private key
            _os.system("chmod go-rwx %s" % privkey)

            # now generate the public key
            cmd = "openssl rsa -pubout -in %s -out %s -passin file:%s" % \
                       (privkey,pubkey,passphrase_file)

            status = _os.system(cmd)

            if status != 0:
                raise KeyManipulationError(
                       "Cannot create the public key (%s)!" % pubkey)

        except:
            # remove any keys that have been generated
            try:
                _os.remove(privkey)
                _os.remove(pubkey)
                _os.rmdir(tmpdir)
            except:
               pass

            raise
        finally:
            # make sure we don't leave the passphrase on disk!
            _os.remove(passphrase_file)

        return (privkey, pubkey)
