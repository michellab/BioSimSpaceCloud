
import json
import os

from Acquire.Service import unpack_arguments, get_service_private_key, \
                            get_trusted_service_info
from Acquire.Service import create_return_value, pack_return_value

from Acquire.Accounting import Accounts


class CreateAccountError(Exception):
    pass


def handler(ctx, data=None, loop=None):
    """This function is called to handle creating accounts for users"""

    status = 0
    message = None
    error = None

    log = []

    args = unpack_arguments(data, get_service_private_key)

    try:
        try:
            user_uid = args["user_uid"]
        except:
            user_uid = None

        try:
            username = args["username"]
        except:
            username = None

        if user_uid is None and username is None:
            raise CreateAccountError("You must supply either the username "
                                     "or user_uid")

        try:
            account_name = args["account_name"]
        except:
            account_name = None

        try:
            description = args["description"]
        except:
            description = None

        if account_name is None or description is None:
            raise CreateAccountError("You must supply both an account name "
                                     "and a description to create an account")

        identity_url = args["identity_url"]
        identity_service = get_trusted_service_info(identity_url)

        if not identity_service.is_identity_service():
            raise CreateAccountError("Cannot add as '%s' is not an identity "
                                     "service" % (identity_url))

        # check that user exists in the identity service
        (username, user_uid) = identity_service.whois(username, user_uid)

        # try to create a 'main' account for this user
        accounts = Accounts(user_uid)
        accounts.create_account(name=account_name, description=description)

        status = 0
        message = "Success"

    except Exception as e:
        error = e

    return_value = create_return_value(status, message, log, error)

    return pack_return_value(return_value, args)

if __name__ == "__main__":
    try:
        from fdk import handle
        handle(handler)
    except Exception as e:
        print("Error running function: %s" % str(e))
        raise
