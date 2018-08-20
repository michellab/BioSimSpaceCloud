
import json
import fdk
import os

from Acquire import ObjectStore, Service, unpack_arguments, call_function, \
                    create_return_value, pack_return_value, \
                    login_to_service_account, get_service_info, \
                    get_service_private_key, MissingServiceAccountError

class AddAccountError(Exception):
    pass

def handler(ctx, data=None, loop=None):
    """This function is called to handle adding accounts
       to this access service. An account is a combination
       of a user_uid, the identity service used to authenticate
       that user, and the accounting service used to
       give permission (and record spend) of users on 
       resources. Note that you can only add users who
       are attached to trusted identity and accounting 
       services
    """

    status = 0
    message = None
    provisioning_uri = None

    log = []

    args = unpack_arguments(data, get_service_private_key)

    try:
        user_uid = args["user_uid"]
        identity_service_url = args["identity_service_url"]        
        accounting_service_url = args["accounting_service_url"]

        # check that the passed services are trusted
        bucket = login_to_service_account()

        identity_service = get_trusted_service_info(identity_service_url)
        accounting_service = get_trusted_service_info(accounting_service_url)
        
        if not identity_service.is_identity_service():
            raise AddAccountError("Cannot add account as '%s' is not an identity "
                                  "service" % (identity_service_url))

        if not accounting_service.is_accounting_service():
       	    raise AddAccountError("Cannot add account as '%s' is not an	accounting "
       	       	       	       	  "service" % (accounting_service_url))

        status = 0
        message = "Success"

    except Exception as e:
        status = -1
        message = "Error %s: %s" % (e.__class__,str(e))

    return_value = create_return_value(status, message, log)
    
    if provisioning_uri:
        return_value["provisioning_uri"] = provisioning_uri

    if log:
        return_value["log"] = log

    return pack_return_value(return_value,args)

if __name__ == "__main__":
    from fdk import handle
    handle(handler)
