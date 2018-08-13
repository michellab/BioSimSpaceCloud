
import json
import fdk

from Acquire import ObjectStore, UserAccount, LoginSession
from identityaccount import loginToIdentityAccount

class InvalidSessionError(Exception):
    pass

def handler(ctx, data=None, loop=None):
    """This function will allow anyone to query the current login
       status of the session with passed UID"""

    # The very first thing to do is make sure that the user 
    # has passed us some valid credentials...
    if not (data and len(data) > 0):
        return    

    status = 0
    message = None
    session_status = None

    try:
        # data is already a decoded unicode string
        data = json.loads(data)

        session_uid = data["session_uid"]
        username = data["username"]

        # generate a sanitised version of the username
        user_account = UserAccount(username)

        # now log into the central identity account to query
        # the current status of this login session
        bucket = loginToIdentityAccount()

        user_session_key = "sessions/%s/%s" % \
                   (user_account.sanitised_name(), session_uid)

        login_session = LoginSession.from_data(
                           ObjectStore.get_object_from_json( bucket, 
                                                             user_session_key ) )

        status = 0
        message = "Success: Status = %s" % login_session.status()
        session_status = login_session.status()

    except Exception as e:
        status = -1
        message = "Error %s: %s" % (e.__class__,str(e))

    response = {}
    response["status"] = status
    response["message"] = message
    
    if session_status:
        response["session_status"] = session_status

    return json.dumps(response).encode("utf-8")

if __name__ == "__main__":
    from fdk import handle
    handle(handler)
