
import json
import os

from Acquire.Service import unpack_arguments, get_service_private_key, \
                            get_trusted_service_info, login_to_service_account
from Acquire.Service import create_return_value, pack_return_value

from Acquire.Accounting import Accounts, Authorisation


class AccountError(Exception):
    pass


def handler(ctx, data=None, loop=None):
    """This function is called to handle requests for information about
       particular accounts"""

    status = 0
    message = None
    error = None

    log = []

    args = unpack_arguments(data, get_service_private_key)

    account = None
    balance_status = None

    try:
        try:
            user_uid = str(args["user_uid"])
        except:
            user_uid = None

        try:
            account_name = str(args["account_name"])
        except:
            account_name = None

        try:
            authorisation = Authorisation.from_data(args["authorisation"])
        except:
            authorisation = None

        try:
            identity_url = str(args["identity_url"])
        except:
            identity_url = None

        if user_uid is None:
            raise AccountError("You must supply the user_uid")

        identity_service = get_trusted_service_info(identity_url)

        if not identity_service.is_identity_service():
            raise AccountError("Cannot add as '%s' is not an "
                               "identity service" % (identity_url))

        # check that user exists in the identity service and get the
        # signing key associated with the passed session UID
        response = identity_service.whois(
                                user_uid=user_uid,
                                session_uid=authorisation.session_uid())

        # check that this authorisation has been correctly
        # signed by the user
        authorisation.verify(response["public_cert"])

        # load the account
        bucket = login_to_service_account()
        account = Accounts(user_uid).get_account(account_name, bucket=bucket)
        balance_status = account.balance_status(bucket=bucket)

        status = 0
        message = "Success"

    except Exception as e:
        error = e

    return_value = create_return_value(status, message, log, error)

    if account:
        return_value["description"] = account.description()
        return_value["overdraft_limit"] = account.get_overdraft_limit()

    if balance_status:
        for key in balance_status.keys():
            return_value[key] = balance_status[key]

    return pack_return_value(return_value, args)


if __name__ == "__main__":
    try:
        from fdk import handle
        handle(handler)
    except Exception as e:
        print("Error running function: %s" % str(e))
        raise
