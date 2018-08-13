
import json
import fdk

from Acquire import ObjectStore, UserAccount, LoginSession
from identityaccount import loginToIdentityAccount

class InvalidLoginError(Exception):
    pass

def prune_expired_sessions(bucket, user_account, root, sessions):
    """This function will scan through all open requests and 
       login sessions and will prune away old, expired or otherwise
       weird sessions. It will also use the ipaddress of the source
       to rate limit or blacklist sources"""

    message = []

    for name in sessions:
        key = "%s/%s" % (root,name)
        request_key = "requests/%s/%s" % (name[:8],name)

        try:
            session = ObjectStore.get_object_from_json(bucket, key)
        except:
            message.append("Session %s does not exist!" % name)
            session = None

        if session:
            should_delete = False

            try:
                session = LoginSession.from_data(session)
                if session.status() == "approved":
                    if session.hours_since_creation() > user_account.login_timeout():
                        should_delete = True
                elif session.status() == "denied" or session.status() == "logged_out":
                    should_delete = True
                else:
                    if session.hours_since_creation() > user_account.login_request_timeout():
                        should_delete = True
            except:
                # this is corrupt - delete it
                should_delete = True

            if should_delete:
                message.append("Deleting expired session '%s'" % key)

                try:
                    ObjectStore.delete_object(bucket, key)
                except:
                    pass

                try:
                    ObjectStore.delete_object(bucket, request_key)
                except:
                    pass

    return message

def handler(ctx, data=None, loop=None):
    """This function will allow a user to request a new session
       that will be validated by the passed public key and public
       signing certificate. This will return a URL that the user
       must connect to to then log in and validate that request.
    """

    # The very first thing to do is make sure that the user 
    # has passed us some valid credentials...
    if not (data and len(data) > 0):
        return    

    status = 0
    message = None
    prune_message = None
    login_url = None
    login_uid = None

    try:
        # data is already a decoded unicode string
        data = json.loads(data)

        username = data["username"]
        public_key = data["public_key"]
        public_cert = data["public_certificate"]

        ip_addr = None
        hostname = None
        login_message = None

        try:
            ip_addr = data["ipaddr"]
        except:
            pass

        try:
            hostname = data["hostname"]
        except:
            pass

        try:
            login_message = data["message"]
        except:
            pass

        # generate a sanitised version of the username
        user_account = UserAccount(username)

        # Now generate a login session for this request
        login_session = LoginSession(public_key, public_cert, ip_addr,
                                     hostname, login_message)

        # now log into the central identity account to record
        # that a request to open a login session has been opened
        bucket = loginToIdentityAccount()

        # first, make sure that the user exists...
        account_key = "accounts/%s" % user_account.sanitised_name()

        try:
            existing_data = ObjectStore.get_object_from_json(bucket, account_key)
        except:
            existing_data = None

        if existing_data is None:
            raise InvalidLoginError("There is no user with name '%s'" % username)

        user_account = UserAccount.from_data(existing_data)

        # first, make sure that the user doens't have too many open
        # login sessions at once - this prevents denial of service
        user_session_root = "sessions/%s" % user_account.sanitised_name()

        open_sessions = ObjectStore.get_all_object_names(bucket, 
                                                         user_session_root)

        # take the opportunity to prune old user login sessions
        prune_message = prune_expired_sessions(bucket, user_account, 
                                               user_session_root, open_sessions)

        # this is the key for the session in the object store
        user_session_key = "%s/%s" % (user_session_root,
                                      login_session.uuid())

        ObjectStore.set_object_from_json( bucket, user_session_key,
                                          login_session.to_data() )

        # we will record a pointer to the request using the short
        # UUID. This way we can give a simple URL. If there is a clash,
        # then we will use the username provided at login to find the
        # correct request from a much smaller pool (likely < 3)
        request_key = "requests/%s/%s" % (login_session.short_uuid(),
                                          login_session.uuid())

        ObjectStore.set_string_object(bucket, request_key, user_account.name())

        status = 0
        login_url = "%s/%s" % (user_account.login_root_url(),
                               login_session.short_uuid())        

        login_uid = login_session.uuid()

        message = "Success: Login via %s" % login_url

    except Exception as e:
        status = -1
        message = "Error %s: %s" % (e.__class__,str(e))

    response = {}
    response["status"] = status
    response["message"] = message
    response["session_uid"] = login_uid

    if login_url:
        response["login_url"] = login_url
    else:
        response["login_url"] = None

    if prune_message:
        response["prune_message"] = prune_message

    return json.dumps(response).encode("utf-8")

if __name__ == "__main__":
    from fdk import handle
    handle(handler)
