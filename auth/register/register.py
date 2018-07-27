
import json
import fdk
import oci

import os
import tempfile
import re

from BioSimSpaceCloud import ObjectStore
from identityaccount import loginToIdentityAccount

class UsernameError(Exception):
    pass

class ExistingAccountError(Exception):
    pass

class WeakPassphraseError(Exception):
    pass

class KeyManipulationError(Exception):
    pass

def sanitiseUsername(username):
    """This function returns a sanitised version of
       the username. This will ensure that the username
       is valid (must be between 3 and 50 characters) and
       will remove anything problematic for the object
       store
    """

    if username is None:
        raise UsernameError("You must pass in a username of some sort!")

    if len(username) < 3 or len(username) > 50:
        raise UsernameError("The username must be between 3 and 50 characters!")

    return "_".join(username.split()).replace("/","") \
              .replace("@","_AT_").replace(".","_DOT_")

def assertStrongPassphrase(passphrase):
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

    if not (re.search(r'[A-Z]', passphrase) and
            re.search(r'[a-z]', passphrase) and
            re.search(r'[0-9]', passphrase)):
        raise WeakPassphraseError("The pass-phrase must contain numbers and "
                                  "upper- and lowercase characters")

    return passphrase

def assertValidPassphrase(user_account, passphrase, mangleFunction=None):
    """This function asserts that the supplied passphrase
       will unlock the passed user_account"""

    passphrase = assertStrongPassphrase(passphrase)

    if mangleFunction:
        passphrase = mangleFunction(passphrase)

    # create a directory to hold all of the keys
    tmpdir = tempfile.mkdtemp()

    passphrase_file = "%s/passphrase" % tmpdir
    privkey = "%s/credentials.pem" % tmpdir
    pubkey = "%s/credentials_public.pem" % tmpdir

    # create a file readable only by this user in the passphrase
    # can be written. Need to do this as passing the passphrase 
    # via a command line argument is not secure - anyone can see it!
    with open(os.open(passphrase_file, 
                      os.O_CREAT | os.O_WRONLY, 0o700), 'w') as FILE:
        FILE.write(passphrase)

    try:
        # now write the account's private key to a file (user readable only)
        with open(os.open(privkey,
                  os.O_CREAT | os.O_WRONLY, 0o700), 'w') as FILE:
            for line in user_account["private_key"]:
                FILE.write(line)

        # now generate the public key
        cmd = "openssl rsa -pubout -in %s -out %s -passin file:%s" % \
                   (privkey,pubkey,passphrase_file)

        status = os.system(cmd)

        if status != 0:
            raise KeyManipulationError("Cannot unlock the public key "
                                       "using the passed passphrase! Invalid password")

    finally:
        # remove any keys that have been generated
        try:
            os.remove(passphrase_file)
            os.remove(privkey)
            os.remove(pubkey)
            os.rmdir(tmpdir)
        except:
            pass


def createKeyPair(passphrase, mangleFunction=None):
    """Create a public/private key pair, with the private
       key encrypted using the passed passphrase"""

    passphrase = assertStrongPassphrase(passphrase)

    if mangleFunction:
        passphrase = mangleFunction(passphrase)

    # create a directory to hold all of the keys
    tmpdir = tempfile.mkdtemp()

    passphrase_file = "%s/passphrase" % tmpdir
    privkey = "%s/credentials.pem" % tmpdir
    pubkey = "%s/credentials_public.pem" % tmpdir

    # create a file readable only by this user in the passphrase
    # can be written. Need to do this as passing the passphrase 
    # via a command line argument is not secure - anyone can see it!
    with open(os.open(passphrase_file, 
                      os.O_CREAT | os.O_WRONLY, 0o700), 'w') as FILE:
        FILE.write(passphrase)

    try:
        # Use openssl to generate the private key
        cmd = "openssl genrsa -out %s -aes128 -passout file:%s 2048" % \
                  (privkey,passphrase_file)

        status = os.system(cmd)

        if status != 0:
            raise KeyManipulationError("Cannot create the private key (%s)!" % privkey)

        # ensure that only we can read the private key
        os.system("chmod go-rwx %s" % privkey)

        # now generate the public key
        cmd = "openssl rsa -pubout -in %s -out %s -passin file:%s" % \
                   (privkey,pubkey,passphrase_file)

        status = os.system(cmd)

        if status != 0:
            raise KeyManipulationError("Cannot create the public key (%s)!" % pubkey)

    except:
        # remove any keys that have been generated
        try:
            os.remove(privkey)
            os.remove(pubkey)
            os.rmdir(tmpdir)
        except:
            pass

        raise

    finally:
        # make sure we don't leave the passphrase on disk!
        os.remove(passphrase_file)

    return (privkey, pubkey)

def handler(ctx, data=None, loop=None):
    """This function will allow a user to register an account with a 
       username and password"""

    # The very first thing to do is make sure that the user 
    # has passed us some valid credentials...
    if not (data and len(data) > 0):
        return    

    status = 0
    message = None

    try:
        data = json.loads(data)

        username = data["username"]
        password = data["password"]

        # generate a sanitised version of the username
        sanitised_username = sanitiseUsername(username)

        # generate the encryption keys using the passed password
        (privkey, pubkey) = createKeyPair(password)

        # now log into the central identity account to either register
        # the user, or to update to a new password
        bucket = loginToIdentityAccount()
        account_key = "accounts/%s" % sanitised_username

        user_account = ObjectStore.get_object_from_json(bucket, account_key)

        message = "Created a new account for '%s'" % username

        if user_account is None:
            user_account = {}
            user_account["username"] = username
            user_account["private_key"] = open(privkey,"r").readlines()
            user_account["public_key"] = open(pubkey, "r").readlines()
            user_account["status"] = "active"

            # save the new account details
            ObjectStore.set_object_from_json(bucket, account_key, user_account)
        else:
            # The account already exists. See if this is a password change
            # request
            old_password = None

            try:
                old_password = data["old_password"]
            except:
                raise ExistingAccountError("An account by this name already exists!")

            if old_password != password:
                # this is a change of password request - validate that
                # the existing password unlocks the existing key
                assertValidPassphrase(user_account, old_password)

                user_account["private_key"] = open(privkey,"r").readlines()
                user_account["public_key"] = open(pubkey,"r").readlines()

                # save the new account details
                ObjectStore.set_object_from_json(bucket, account_key, user_account)

                message = "Updated the password for '%s'" % username
            else:
                message = "No need to change account '%s'" % username

        # it is acceptable to update the account information
        ObjectStore.set_object_from_json(bucket, account_key, user_account)

        status = 0

    except Exception as e:
        status = -1
        message = "Error: %s" % str(e)

    response = {}
    response["status"] = status
    response["message"] = message

    return json.dumps(response)

if __name__ == "__main__":
    from fdk import handle
    handle(handler)
