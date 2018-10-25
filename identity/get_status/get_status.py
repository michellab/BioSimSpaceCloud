
import json

from Acquire.Service import get_service_private_key, unpack_arguments, \
                            login_to_service_account
from Acquire.Service import create_return_value, pack_return_value, \
                            start_profile, end_profile

from Acquire.ObjectStore import ObjectStore

from Acquire.Identity import UserAccount, LoginSession


class InvalidSessionError(Exception):
    pass


def handler(ctx, data=None, loop=None):
    """This function will allow anyone to query the current login
       status of the session with passed UID"""

    pr = start_profile()

    status = 0
    message = None
    session_status = None

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

        try:
            login_session = LoginSession.from_data(
                               ObjectStore.get_object_from_json(
                                   bucket, user_session_key))
        except:
            login_session = None

        if login_session is None:
            user_session_key = "expired_sessions/%s/%s" % \
                                    (user_account.sanitised_name(),
                                     session_uid)

            login_session = LoginSession.from_data(
                                ObjectStore.get_object_from_json(
                                    bucket, user_session_key))

        if login_session is None:
            raise InvalidSessionError(
                    "Cannot find the session '%s'" % session_uid)

        status = 0
        message = "Success: Status = %s" % login_session.status()
        session_status = login_session.status()

    except Exception as e:
        status = -1
        message = "Error %s: %s" % (e.__class__, str(e))

    return_value = create_return_value(status, message, log)

    if session_status:
        return_value["session_status"] = session_status

    end_profile(pr, return_value)

    return pack_return_value(return_value, args)

if __name__ == "__main__":
    try:
        from fdk import handle
        handle(handler)
    except Exception as e:
        print("Error running function: %s" % str(e))
        raise
