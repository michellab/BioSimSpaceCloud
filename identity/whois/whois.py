
import json
import fdk

from Acquire import ObjectStore, UserAccount, LoginSession
from identityaccount import loginToIdentityAccount

class WhoisLookupError(Exception):
    pass

def handler(ctx, data=None, loop=None):
    """This function will allow anyone to query who matches
       the passed UID or username (map from one to the other)"""

    if not (data and len(data) > 0):
        return    

    status = 0
    message = None
    uuid = None
    username = None

    log = []

    try:
        # data is already a decoded unicode string
        data = json.loads(data)

        try:
            uuid = data["uuid"]
        except:
            pass

        try:
            username = data["username"]
        except:
            pass

        if uuid is None and username is None:
            raise WhoisLookupError("You must supply either a username or "
                          "uuid to look up...") 

        elif uuid is None:
            # look up the uuid from the username
            user_account = UserAccount(username)
            bucket = loginToIdentityAccount()
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
            bucket = loginToIdentityAccount()

            uuid_key = "whois/%s" % uuid

            try:
                username = ObjectStore.get_string_object(bucket, uuid_key)
            except:
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

    response = {}
    response["status"] = status
    response["message"] = message
    
    if uuid:
        response["uuid"] = uuid

    if username:
        response["username"] = username

    if log:
        response["log"] = log

    return json.dumps(response).encode("utf-8")

if __name__ == "__main__":
    from fdk import handle
    handle(handler)
