
import json
import fdk

from Acquire import ObjectStore, UserAccount, LoginSession, bytes_to_string
from accessaccount import loginToAccessAccount

class RequestBucketError(Exception):
    pass

def handler(ctx, data=None, loop=None):
    """This function is used to request access to a bucket for 
       data in the object store. The user can request read-only
       or read-write access. Access is granted based on a permission
       list"""

    if not (data and len(data) > 0):
        return    

    status = 0
    message = None

    access_token = None

    try:
        # data is already a decoded unicode string
        data = json.loads(data)

        user_uuid = data["user_uuid"]
        identity_service = data["identity_service"]
        request_data = data["request"]
        signature = string_to_bytes( data["signature"] )

        # log into the central access account
        bucket = loginToAccessAccount()

        # is the identity service supplied by the user one that we trust?
        

        # first, ask the identity service to give us the public
        # certificate and signing certificate for this user.

        user_session_key = "sessions/%s/%s" % \
                   (user_account.sanitised_name(), session_uid)

        login_session = LoginSession.from_data(
                           ObjectStore.get_object_from_json( bucket, 
                                                             user_session_key ) )

        # only send valid keys if the user had logged in!
        if not login_session.is_approved():
            raise InvalidSessionError( "You cannot get the keys for a session "
                    "for which the user has not logged in!" )

        public_key = bytes_to_string(login_session.public_key())
        public_cert = bytes_to_string(login_session.public_certificate())

        status = 0
        message = "Success: Status = %s" % login_session.status()

    except Exception as e:
        status = -1
        message = "Error %s: %s" % (e.__class__,str(e))

    response = {}
    response["status"] = status
    response["message"] = message
    
    if public_key:
        response["public_key"] = public_key

    if public_cert:
        response["public_cert"] = public_cert

    return json.dumps(response).encode("utf-8")

if __name__ == "__main__":
    from fdk import handle
    handle(handler)
