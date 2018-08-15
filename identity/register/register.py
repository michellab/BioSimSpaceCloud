
import json
import fdk

from Acquire import ObjectStore, Keys, UserAccount, PrivateKey, PublicKey, OTP
from identityaccount import loginToIdentityAccount

class ExistingAccountError(Exception):
    pass

def handler(ctx, data=None, loop=None):
    """This function will allow a user to register an account with a 
       username and password"""

    # The very first thing to do is make sure that the user 
    # has passed us some valid credentials...
    if not (data and len(data) > 0):
        return    

    status = 0
    message = None
    provisioning_uri = None

    try:
        data = json.loads(data)

        username = data["username"]
        password = data["password"]

        # generate a sanitised version of the username
        user_account = UserAccount(username)

        # generate the encryption keys and otp secret
        privkey = PrivateKey()
        pubkey = privkey.public_key()
        otp = OTP()

        provisioning_uri = otp.provisioning_uri(username)

        # save the encrypted private key (encrypted using the user's password)
        # and encrypted OTP secret (encrypted using the public key)
        user_account.set_keys(privkey.bytes(password), pubkey.bytes(), 
                              otp.encrypt(pubkey))

        # remove the key and password from memory
        privkey = None
        password = None

        # now log into the central identity account to either register
        # the user, or to update to a new password
        bucket = loginToIdentityAccount()
        account_key = "accounts/%s" % user_account.sanitised_name()

        try:
            existing_data = ObjectStore.get_object_from_json(bucket, account_key)
        except:
            existing_data = None

        message = "Created a new account for '%s'" % username
        status = 0

        if existing_data is None:
            # save the new account details
            ObjectStore.set_object_from_json(bucket, account_key, 
                                             user_account.to_data())
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
                user_account = UserAccount.from_data(existing_data)

                testkey = PrivateKey.read_bytes(user_account.private_key(),
                                                old_password)

                # decrypt the old secret
                old_secret = testkey.decrypt(user_account.otp_secret())

                # now encrypt the secret with the new key
                new_key = PublicKey.read_bytes(pubkey)
                new_secret = new_key.encrypt(old_secret)

                user_account.set_keys(privkey,pubkey,new_secret)

                # save the new account details
                ObjectStore.set_object_from_json(bucket, account_key, 
                                                 user_account.to_data())

                message = "Updated the password for '%s'" % username
            else:
                message = "No need to change account '%s'" % username

    except Exception as e:
        status = -1
        message = "Error: %s" % str(e)

    response = {}
    response["status"] = status
    response["message"] = message

    if provisioning_uri:
        response["provisioning_uri"] = provisioning_uri

    return json.dumps(response).encode("utf-8")

if __name__ == "__main__":
    from fdk import handle
    handle(handler)
