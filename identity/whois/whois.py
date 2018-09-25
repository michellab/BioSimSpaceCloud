
import json

from Acquire.Service import unpack_arguments, get_service_private_key, \
                            login_to_service_account
from Acquire.Service import create_return_value, pack_return_value

from Acquire.ObjectStore import ObjectStore

from Acquire.Identity import UserAccount, LoginSession


class WhoisLookupError(Exception):
    pass


class InvalidSessionError(Exception):
    pass


def handler(ctx, data=None, loop=None):
    """This function will allow anyone to query who matches
       the passed UID or username (map from one to the other)"""

    status = 0
    message = None
    user_uid = None
    username = None
    public_key = None
    public_cert = None

    log = []

    args = unpack_arguments(data, get_service_private_key)

    try:
        try:
            user_uid = args["user_uid"]
        except:
            pass

        try:
            username = args["username"]
        except:
            pass

        try:
            session_uid = args["session_uid"]
        except:
            session_uid = None

        bucket = None
        user_account = None

        if user_uid is None and username is None:
            raise WhoisLookupError(
                "You must supply either a username or user_uid to look up...")

        elif user_uid is None:
            # look up the user_uid from the username
            user_account = UserAccount(username)
            bucket = login_to_service_account()
            user_key = "accounts/%s" % user_account.sanitised_name()

            try:
                user_account = UserAccount.from_data(
                                 ObjectStore.get_object_from_json(bucket,
                                                                  user_key))
            except Exception as e:
                log.append("Error looking up account by name: %s" % str(e))
                raise WhoisLookupError(
                    "Cannot find an account for name '%s'" % username)

            user_uid = user_account.uid()

        elif username is None:
            # look up the username from the uuid
            bucket = login_to_service_account()

            uid_key = "whois/%s" % user_uid

            try:
                username = ObjectStore.get_string_object(bucket, uid_key)
            except Exception as e:
                log.append("Error looking up account by user_uid: %s" % str(e))
                raise WhoisLookupError(
                    "Cannot find an account for user_uid '%s'" % user_uid)

        else:
            raise WhoisLookupError(
                "You must only supply one of the username "
                "or user_uid to look up - not both!")

        if session_uid:
            # now look up the public signing key for this session, if it is
            # a valid login session
            if user_account is None:
                user_account = UserAccount(username)

            user_session_key = "sessions/%s/%s" % \
                (user_account.sanitised_name(), session_uid)

            login_session = LoginSession.from_data(
                               ObjectStore.get_object_from_json(
                                   bucket, user_session_key))

            # only send valid keys if the user had logged in!
            if not login_session.is_approved():
                raise InvalidSessionError(
                        "You cannot get the keys for a session "
                        "for which the user has not logged in!")

            public_key = login_session.public_key().to_data()
            public_cert = login_session.public_certificate().to_data()

        status = 0
        message = "Success"

    except Exception as e:
        status = -1
        message = "Error %s: %s" % (e.__class__, str(e))

    return_value = create_return_value(status, message, log)

    if user_uid:
        return_value["user_uid"] = user_uid

    if username:
        return_value["username"] = username

    if public_key:
        return_value["public_key"] = public_key

    if public_cert:
        return_value["public_cert"] = public_cert

    return pack_return_value(return_value, args)


if __name__ == "__main__":
    try:
        from fdk import handle
        handle(handler)
    except Exception as e:
        print("Error running function: %s" % str(e))
        raise
