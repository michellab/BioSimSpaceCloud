
import json
import os

from Acquire.Service import unpack_arguments, get_service_private_key, \
                            get_trusted_service_info, login_to_service_account
from Acquire.Service import create_return_value, pack_return_value

from Acquire.Accounting import Accounts, Authorisation


class ListAccountsError(Exception):
    pass


def handler(ctx, data=None, loop=None):
    """This function is called to handle requests for the UIDs of accounts"""

    status = 0
    message = None
    error = None

    log = []

    args = unpack_arguments(data, get_service_private_key)

    account_uids = None

    try:
        try:
            user_uid = str(args["user_uid"])
        except:
            user_uid = None

        try:
            account_name = str(args["user_name"])
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

        if user_uid is None or identity_url is None or authorisation is None:
            raise ListAccountsError("You must supply either the username "
                                    "or user_uid")

        identity_service = get_trusted_service_info(identity_url)

        if not identity_service.is_identity_service():
            raise ListAccountsError("Cannot add as '%s' is not an identity "
                                    "service" % (identity_url))

        # check that user exists in the identity service and get the
        # signing key associated with the passed session UID
        response = identity_service.whois(
                                    user_uid=user_uid,
                                    session_uid=authorisation.session_uid())

        # check that this authorisation has been correctly signed by the user
        authorisation.verify(response["public_cert"])

        # try to create a 'main' account for this user
        account_uids = {}
        accounts = Accounts(user_uid)

        if account_name is None:
            bucket = login_to_service_account()
            account_names = accounts.list_accounts(bucket=bucket)

            for account_name in account_names:
                account = accounts.get_account(account_name, bucket=bucket)
                account_uids[account.uid()] = account.name()

        else:
            account = accounts.get_account(account_name)
            account_uids[account.uid()] = account.name()

        status = 0
        message = "Success"

    except Exception as e:
        error = e

    return_value = create_return_value(status, message, log, error)

    if account_uids:
        return_value["account_uids"] = account_uids

    return pack_return_value(return_value, args)


if __name__ == "__main__":
    try:
        from fdk import handle
        handle(handler)
    except Exception as e:
        print("Error running function: %s" % str(e))
        raise
