
import json

from Acquire.Service import unpack_arguments, get_service_private_key, login_to_service_account
from Acquire.Service import create_return_value, pack_return_value

from Acquire.ObjectStore import ObjectStore

from Acquire.Identity import UserAccount

class WhoisLookupError(Exception):
    pass

def handler(ctx, data=None, loop=None):
    """This function will allow anyone to query who matches
       the passed UID or username (map from one to the other)"""

    status = 0
    message = None
    uuid = None
    username = None

    log = []

    args = unpack_arguments(data, get_service_private_key)

    try:
        try:
            uuid = args["uuid"]
        except:
            pass

        try:
            username = args["username"]
        except:
            pass

        if uuid is None and username is None:
            raise WhoisLookupError("You must supply either a username or "
                          "uuid to look up...") 

        elif uuid is None:
            # look up the uuid from the username
            user_account = UserAccount(username)
            bucket = login_to_service_account()
            user_key = "accounts/%s" % user_account.sanitised_name()

            try:
                user_account = UserAccount.from_data(
                                 ObjectStore.get_object_from_json( bucket,
                                                                   user_key ) )
            except Exception as e:
                log.append("Error looking up account by name: %s" % str(e))
                raise WhoisLookupError("Cannot find an account for name '%s'" % \
                                          username)

            uuid = user_account.uuid()

        elif username is None:
            # look up the username from the uuid
            bucket = login_to_service_account()

            uuid_key = "whois/%s" % uuid

            try:
                username = ObjectStore.get_string_object(bucket, uuid_key)
            except Exception as e:
                log.append("Error looking up account by uuid: %s" % str(e))
                raise WhoisLookupError("Cannot find an account for uuid '%s'" % \
                                           uuid)

        else:
            raise WhoisLookupError("You must only supply one of the username "
                        "or uuid to look up - not both!")

        status = 0
        message = "Success"

    except Exception as e:
        status = -1
        message = "Error %s: %s" % (e.__class__,str(e))

    return_value = create_return_value(status, message, log)

    if uuid:
        return_value["uuid"] = uuid

    if username:
        return_value["username"] = username

    return pack_return_value(return_value, args)

if __name__ == "__main__":
    try:
        from fdk import handle
        handle(handler)
    except Exception as e:
        print("Error running function: %s" % str(e))
        raise
