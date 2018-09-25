
import json
import os

from Acquire.Service import unpack_arguments, get_service_private_key, \
                            get_trusted_service_info
from Acquire.Service import create_return_value, pack_return_value

from Acquire.Accounting import Accounts, Authorisation


class CreateAccountError(Exception):
    pass


def handler(ctx, data=None, loop=None):
    """This function is called to handle creating accounts for users"""

    status = 0
    message = None
    error = None

    log = []

    args = unpack_arguments(data, get_service_private_key)

    account_uid = None

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

        try:
            authorisation = Authorisation.from_data(args["authorisation"])
        except:
            authorisation = None

        if account_name is None or description is None \
                or authorisation is None:
            raise CreateAccountError("You must supply both an account name "
                                     "and a description to create an account")

        identity_url = args["identity_url"]
        identity_service = get_trusted_service_info(identity_url)

        if not identity_service.is_identity_service():
            raise CreateAccountError("Cannot add as '%s' is not an identity "
                                     "service" % (identity_url))

        # check that user exists in the identity service and get the
        # signing key associated with the passed session UID
        response = identity_service.whois(
                                    user_uid=user_uid,
                                    session_uid=authorisation.session_uid())

        # check that this authorisation has been correctly signed by the user
        authorisation.verify(response["public_cert"])

        # try to create a 'main' account for this user
        accounts = Accounts(user_uid)
        account = accounts.create_account(name=account_name,
                                          description=description)

        account_uid = account.uid()

        status = 0
        message = "Success"

    except Exception as e:
        error = e

    return_value = create_return_value(status, message, log, error)

    if account_uid:
        return_value["account_uid"] = account_uid

    return pack_return_value(return_value, args)

if __name__ == "__main__":
    try:
        from fdk import handle
        handle(handler)
    except Exception as e:
        print("Error running function: %s" % str(e))
        raise
