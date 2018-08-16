
import json as _json
import oci as _oci
import os as _os

from Acquire import Account as _Account

class AccountingAccountError(Exception):
    """Used for errors associated with logging into or
       using the central Accounting Account"""
    pass

def loginToAccountingAccount():
    """This function logs into the account of the primary accounting
       manager. This is the central account that has access to 
       all accounting resources and which can authorise the billing
       of access to resource on the object store. Obviously this is
       a powerful account, so only log into it if you need it!!!

       The login information should not be put into a public 
       repository or stored in plain text. In this case,
       the login information is held in an environment variable
       (which should be encrypted or hidden in some way...)
    """

    # get the login information in json format from
    # the LOGIN_JSON environment variable
    accounting_json = _os.getenv("LOGIN_JSON")
    accounting_data = None

    # get the bucket information in json format from
    # the BUCKET_JSON environment variable
    bucket_json = _os.getenv("BUCKET_JSON")
    bucket_data = None

    if bucket_json and len(bucket_json) > 0:
        try:
            bucket_data = _json.loads(bucket_json)
            bucket_json = None
        except:
            raise AccountingAccountError(
             "Cannot decode the bucket information for the central accounting account")
    else:
        raise AccountingAccountError("You must supply valid bucket data!")

    if accounting_json and len(accounting_json) > 0:
        try:
            accounting_data = _json.loads(accounting_json)
            accounting_json = None
        except:
            raise AccountingAccountError(
             "Cannot decode the login information for the central accounting account")
    else:
        raise AccountingAccountError("You must supply valid login data!")

    # now login and create/load the bucket for this account
    try:
        return _Account.create_and_connect_to_bucket(accounting_data,
                                                     bucket_data["compartment"],
                                                     bucket_data["bucket"])
    except Exception as e:
        raise AccountingAccountError(
             "Error connecting to the accounting account: %s" % str(e))
