
import json
import fdk
import os

from Acquire import ObjectStore, Service, unpack_arguments, call_function, \
                    create_return_value, pack_return_value, \
                    login_to_service_account, get_service_info, \
                    get_service_private_key, MissingServiceAccountError, \
                    get_trusted_service_info

class AddUserError(Exception):
    pass

def handler(ctx, data=None, loop=None):
    """This function is called to handle adding users
       to this accounting service. 
    """

    status = 0
    message = None
    error = None

    log = []

    args = unpack_arguments(data, get_service_private_key)

    try:
        try:
            user_uid = args["user_uid"]
        except:
            user_uid = None

        try:
            username = args["username"]
        except:
            username = None

        if user_uid is None and username is None:
            raise AddUserError("You must supply either the username or user_uid")

        identity_service_url = args["identity_service_url"]        
        identity_service = get_trusted_service_info(identity_service_url)
        
        if not identity_service.is_identity_service():
            raise AddUserError("Cannot add as '%s' is not an identity "
                               "service" % (identity_service_url))

        # check that user exists in the identity service
        (username, user_uid) = identity_service.whois(username, user_uid)

        # save this username and uid to the object store
        

        status = 0
        message = "Success"

    except Exception as e:
        error = e

    return_value = create_return_value(status, message, log, error)
    
    return pack_return_value(return_value,args)

if __name__ == "__main__":
    from fdk import handle
    handle(handler)
