
import json
import fdk

from Acquire import ObjectStore, Keys, UserAccount
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

    try:
        data = json.loads(data)

        username = data["username"]
        password = data["password"]

        # generate a sanitised version of the username
        user_account = UserAccount(username)

        # generate the encryption keys using the passed password
        (privkey, pubkey, secret) = Keys.create_key_pair(password, create_secret=True)
        user_account.set_keys(privkey, pubkey, secret)

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

                Keys.assert_valid_passphrase(user_account.private_key(), 
                                             old_password)

                user_account.set_keys(privkey,pubkey,secret)

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

    return json.dumps(response).encode("utf-8")

if __name__ == "__main__":
    from fdk import handle
    handle(handler)
