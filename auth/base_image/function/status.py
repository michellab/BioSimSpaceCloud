
import json
import fdk
import oci

import os

from BioSimSpaceCloud import Account

class IdentityAccountError(Exception):
    """Used for errors associated with logging into or
       using the central Identity Account"""
    pass

def loginToIdentityAccount():
    """This function logs into the account of the primary identity
       manager. This is the central account that has access to 
       all user credentials and which can authorise the creation
       of delegated accounts on the object store. Obviously this is
       a powerful account, so only log into it if you need it!!!

       The login information should not be put into a public 
       repository or stored in plain text. In this case,
       the login information is held in an environment variable
       (which should be encrypted or hidden in some way...)
    """

    # get the login information in json format from
    # the LOGIN_JSON environment variable
    identity_json = os.getenv("LOGIN_JSON")
    identity_data = None

    # get the bucket information in json format from
    # the BUCKET_JSON environment variable
    bucket_json = os.getenv("BUCKET_JSON")
    bucket_data = None

    if bucket_json and len(bucket_json) > 0:
        try:
            bucket_data = json.loads(bucket_json)
            bucket_json = None
        except:
            raise IdentityAccountError(
             "Cannot decode the bucket information for the central identity account")
    else:
        raise IdentityAccountError("You must supply valid bucket data!")

    if identity_json and len(identity_json) > 0:
        try:
            identity_data = json.loads(identity_json)
            identity_json = None
        except:
            raise IdentityAccountError(
             "Cannot decode the login information for the central identity account")
    else:
        raise IdentityAccountError("You must supply valid login data!")

    # now login and create/load the bucket for this account
    try:
        return Account.create_and_connect_to_bucket(identity_data,
                                                    bucket_data["compartment"],
                                                    bucket_data["bucket"])
    except Exception as e:
        raise IdentityAccountError(
             "Error connecting to the identity account: %s" % str(e))

def handler(ctx, data=None, loop=None):
    """This function will read in json data that identifies the 
       user and supplied password. The user's pem key will be
       retrieved from the object store, password checked, and,
       if passed, then this will be returned as a response"""

    # The first step is to log into the primary identity account.
    identity_client = loginToIdentityAccount()

    key = None

    if data and len(data) > 0:
        try:
            data = json.loads(data)

            username = data["username"]
            password = data["password"]

            status = -1
            message = "Either this user does not exist or the password is incorrect"

        except Exception as e:
            status = -2
            message = str(e)
    else:
        status = -1
        message = "No username so no data to check"

    response = {}
    response["status"] = status
    response["message"] = message
    response["key"] = key

    return json.dumps(response)

if __name__ == "__main__":
    from fdk import handle
    handle(handler)
