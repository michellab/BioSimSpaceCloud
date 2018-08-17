
import json
import fdk

from Acquire import ObjectStore, UserAccount, LoginSession, bytes_to_string, \
                    Service, unpack_arguments, \
                    create_return_value, pack_return_value, \
                    login_to_service_account, get_service_info, \
                    get_service_private_key

class InvalidSessionError(Exception):
    pass

def handler(ctx, data=None, loop=None):
    """This function will allow anyone to obtain the public
       keys for the passed login session of a user with
       a specified login UID"""

    status = 0
    message = None

    public_key = None
    public_cert = None

    log = []

    args = unpack_arguments(data, get_service_private_key)

    try:
        session_uid = args["session_uid"]
        username = args["username"]

        # generate a sanitised version of the username
        user_account = UserAccount(username)

        # now log into the central identity account to query
        # the current status of this login session
        bucket = login_to_service_account()

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

    return_value = create_return_value(status, message, log)    

    if public_key:
        return_value["public_key"] = public_key

    if public_cert:
        return_value["public_cert"] = public_cert

    return pack_return_value(return_value, args)

if __name__ == "__main__":
    from fdk import handle
    handle(handler)
