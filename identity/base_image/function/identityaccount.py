
import json as _json
import oci as _oci
import os as _os

from Acquire import Account as _Account

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
    identity_json = _os.getenv("LOGIN_JSON")
    identity_data = None

    # get the bucket information in json format from
    # the BUCKET_JSON environment variable
    bucket_json = _os.getenv("BUCKET_JSON")
    bucket_data = None

    if bucket_json and len(bucket_json) > 0:
        try:
            bucket_data = _json.loads(bucket_json)
            bucket_json = None
        except:
            raise IdentityAccountError(
             "Cannot decode the bucket information for the central identity account")
    else:
        raise IdentityAccountError("You must supply valid bucket data!")

    if identity_json and len(identity_json) > 0:
        try:
            identity_data = _json.loads(identity_json)
            identity_json = None
        except:
            raise IdentityAccountError(
             "Cannot decode the login information for the central identity account")
    else:
        raise IdentityAccountError("You must supply valid login data!")

    # now login and create/load the bucket for this account
    try:
        return _Account.create_and_connect_to_bucket(identity_data,
                                                     bucket_data["compartment"],
                                                     bucket_data["bucket"])
    except Exception as e:
        raise IdentityAccountError(
             "Error connecting to the identity account: %s" % str(e))
