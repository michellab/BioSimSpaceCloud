
import json
import datetime

from Acquire.Service import get_service_private_key, unpack_arguments, \
                            login_to_service_account
from Acquire.Service import create_return_value, pack_return_value

from Acquire.Identity import UserAccount, LoginSession

from Acquire.ObjectStore import ObjectStore


class LoginError(Exception):
    pass


def handler(ctx, data=None, loop=None):
    """This function is called by the user to log in and validate
       that a session is authorised to connect"""

    status = 0
    message = None
    provisioning_uri = None
    log = []

    args = unpack_arguments(data, get_service_private_key)

    try:
        short_uid = args["short_uid"]
        username = args["username"]
        password = args["password"]
        otpcode = args["otpcode"]

        try:
            remember_device = args["remember_device"]
        except:
            remember_device = False

        # create the user account for the user
        user_account = UserAccount(username)

        # log into the central identity account to query
        # the current status of this login session
        bucket = login_to_service_account()

        # locate the session referred to by this uid
        base_key = "requests/%s" % short_uid
        session_keys = ObjectStore.get_all_object_names(bucket, base_key)

        # try all of the sessions to find the one that the user
        # may be referring to...
        login_session_key = None
        request_session_key = None

        for session_key in session_keys:
            request_session_key = "%s/%s" % (base_key, session_key)
            session_user = ObjectStore.get_string_object(
                bucket, request_session_key)

            # did the right user request this session?
            if user_account.name() == session_user:
                if login_session_key:
                    # this is an extremely unlikely edge case, whereby
                    # two login requests within a 30 minute interval for the
                    # same user result in the same short UID. This should be
                    # signified as an error and the user asked to create a
                    # new request
                    raise LoginError(
                        "You have found an extremely rare edge-case "
                        "whereby two different login requests have randomly "
                        "obtained the same short UID. As we can't work out "
                        "which request is valid, the login is denied. Please "
                        "create a new login request, which will then have a "
                        "new login request UID")
                else:
                    login_session_key = session_key

        if not login_session_key:
            raise LoginError(
                "There is no active login request with the "
                "short UID '%s' for user '%s'" % (short_uid, username))

        login_session_key = "sessions/%s/%s" % (user_account.sanitised_name(),
                                                login_session_key)

        # fully load the user account from the object store so that we
        # can validate the username and password
        try:
            account_key = "accounts/%s" % user_account.sanitised_name()
            user_account = UserAccount.from_data(
                ObjectStore.get_object_from_json(bucket, account_key))
        except Exception as e:
            log.append(str(e))
            raise LoginError("No account available with username '%s'" %
                             username)

        # now try to log into this account using the supplied
        # password and one-time-code
        try:
            _provisioning_uri = user_account.validate_password(
                                        password, otpcode, remember_device)
        except:
            # don't leak info about why validation failed
            raise LoginError("The password or OTP code is incorrect")

        # the user is valid - load up the actual login session
        login_session = LoginSession.from_data(
                           ObjectStore.get_object_from_json(bucket,
                                                            login_session_key))

        # we must record the session against which this otpcode has
        # been validated. This is to stop us validating an otpcode more than
        # once (e.g. if the password and code have been intercepted).
        # Any sessions validated using the same code should be treated
        # as immediately suspcious
        otproot = "otps/%s" % user_account.sanitised_name()
        sessions = ObjectStore.get_all_strings(bucket, otproot)

        utcnow = datetime.datetime.utcnow()

        for session in sessions:
            otpkey = "%s/%s" % (otproot, session)
            otpstring = ObjectStore.get_string_object(bucket, otpkey)

            (timestamp, code) = otpstring.split("|||")

            # remove all codes that are more than 10 minutes old. The
            # otp codes are only valid for 3 minutes, so no need to record
            # codes that have been used that are older than that...
            timedelta = utcnow - datetime.datetime.fromtimestamp(
                                                        float(timestamp))

            if timedelta.seconds > 600:
                try:
                    ObjectStore.delete_object(bucket, otpkey)
                    log.append("Removed old otp %s" % otpkey)
                except Exception as e:
                    log.append("Error removing %s: %s" % (otpkey, str(e)))

            elif code == str(otpcode):
                # Low probability there is some recycling,
                # but very suspicious if the code was validated within the last
                # 10 minutes... (as 3 minute timeout of a code)

                suspect_key = "sessions/%s/%s" % (
                    user_account.sanitised_name(), session)

                suspect_session = None

                try:
                    suspect_session = LoginSession.from_data(
                          ObjectStore.get_object_from_json(bucket,
                                                           suspect_key))
                except Exception as e:
                    log.append("Cannot load suspect session '%s': %s" %
                               (suspect_key, str(e)))

                if suspect_session:
                    suspect_session.set_suspicious()
                    ObjectStore.set_object_from_json(bucket, suspect_key,
                                                     suspect_session.to_data())

                raise LoginError(
                    "Cannot authorise the login as the one-time-code "
                    "you supplied has already been used within the last 10 "
                    "minutes. The chance of this happening is really low, so "
                    "we are treating this as a suspicious event. You need to "
                    "try another code. Meanwhile, the other login that used "
                    "this code has been put into a 'suspicious' state.")

        # record the value and timestamp of when this otpcode was used
        otpkey = "%s/%s" % (otproot, login_session.uuid())
        otpstring = "%s|||%s" % (datetime.datetime.utcnow().timestamp(),
                                 otpcode)

        ObjectStore.set_string_object(bucket, otpkey, otpstring)

        login_session.set_approved()

        # write this session back to the object store
        ObjectStore.set_object_from_json(bucket, login_session_key,
                                         login_session.to_data())

        # finally, remove this from the list of requested logins
        try:
            ObjectStore.delete_object(bucket, request_session_key)
        except Exception as e:
            log.append(str(e))
            pass

        status = 0
        message = "Success: Status = %s" % login_session.status()
        provisioning_uri = _provisioning_uri

    except Exception as e:
        status = -1
        message = "Error %s: %s" % (e.__class__, str(e))

    return_value = create_return_value(status, message, log)

    if provisioning_uri:
        return_value["provisioning_uri"] = provisioning_uri

    return pack_return_value(return_value, args)

if __name__ == "__main__":
    try:
        from fdk import handle
        handle(handler)
    except Exception as e:
        print("Error running function: %s" % str(e))
        raise
