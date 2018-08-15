
import json
import fdk

from Acquire import ObjectStore, UserAccount, LoginSession, bytes_to_string
from identityaccount import loginToIdentityAccount

class LoginError(Exception):
    pass

def handler(ctx, data=None, loop=None):
    """This function is called by the user to log in and validate
       that a session is authorised to connect"""

    if not (data and len(data) > 0):
        return    

    status = 0
    message = None
    log = []

    try:
        # data is already a decoded unicode string
        data = json.loads(data)

        short_uid = data["short_uid"]
        username = data["username"]
        password = data["password"]
        otpcode = data["otpcode"]

        # create the user account for the user
        user_account = UserAccount(username)

        # log into the central identity account to query
        # the current status of this login session
        bucket = loginToIdentityAccount()

        # locate the session referred to by this uid
        base_key = "requests/%s" % short_uid
        session_keys = ObjectStore.get_all_object_names(bucket, base_key)

        # try all of the sessions to find the one that the user
        # may be referring to...
        login_session_key = None
        request_session_key = None

        for session_key in session_keys:
            request_session_key = "%s/%s" % (base_key,session_key)
            session_user = ObjectStore.get_string_object(bucket,request_session_key)

            # did the right user request this session?
            if user_account.name() == session_user:
                if login_session_key:
                    # this is an extremely unlikely edge case, whereby 
                    # two login requests within a 30 minute interval for the
                    # same user result in the same short UID. This should be
                    # signified as an error and the user asked to create a
                    # new request
                    raise LoginError("You have found an extremely rare edge-case "
                        "whereby two different login requests have randomly "
                        "obtained the same short UID. As we can't work out "
                        "which request is valid, the login is denied. Please "
                        "create a new login request, which will then have a new "
                        "login request UID")
                else:
                    login_session_key = session_key

        if not login_session_key:
            raise LoginError("There is no active login request with the "
                   "short UID '%s' for user '%s'" % (short_uid,username))

        login_session_key = "sessions/%s/%s" % (user_account.sanitised_name(),
                                                login_session_key)

        # fully load the user account from the object store so that we 
        # can validate the username and password
        try:
            account_key = "accounts/%s" % user_account.sanitised_name()
            user_account = UserAccount.from_data(
                              ObjectStore.get_object_from_json(bucket, account_key))
        except Exception as e:
            log.append(str(e))
            raise LoginError("No account available with username '%s'" % username)

        # now try to log into this account using the supplied
        # password and one-time-code
        user_account.validate_password(password, otpcode)

        # the user is valid - load up the actual login session
        login_session = LoginSession.from_data(
                           ObjectStore.get_object_from_json(bucket,
                                                            login_session_key) )
        
        login_session.set_approved()

        # write this session back to the object store
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

    except Exception as e:
        status = -1
        message = "Error %s: %s" % (e.__class__,str(e))

    response = {}
    response["status"] = status
    response["message"] = message

    if len(log) > 0:
        response["log"] = log
    
    return json.dumps(response).encode("utf-8")

if __name__ == "__main__":
    from fdk import handle
    handle(handler)
