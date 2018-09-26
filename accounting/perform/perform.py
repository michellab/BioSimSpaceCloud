
import json
import os

from Acquire.Service import unpack_arguments, get_service_private_key, \
                            get_trusted_service_info, login_to_service_account
from Acquire.Service import create_return_value, pack_return_value

from Acquire.Accounting import Account, Accounts, Authorisation, \
                               Transaction, Ledger


class TransactionError(Exception):
    pass


def handler(ctx, data=None, loop=None):
    """This function is called to handle requests to perform transactions
       between accounts
    """

    status = 0
    message = None
    error = None

    log = []

    args = unpack_arguments(data, get_service_private_key)

    transaction_records = None

    try:
        try:
            debit_account_uid = str(args["debit_account_uid"])
        except:
            debit_account_uid = None

        try:
            credit_account_uid = str(args["credit_account_uid"])
        except:
            credit_account_uid = None

        try:
            authorisation = Authorisation.from_data(args["authorisation"])
        except:
            authorisation = None

        try:
            transaction = Transaction.from_data(args["transaction"])
        except:
            transaction = None

        try:
            is_provisional = bool(args["is_provisional"])
        except:
            is_provisional = None

        if debit_account_uid is None:
            raise TransactionError("You must supply the account UID "
                                   "for the debit account")

        if credit_account_uid is None:
            raise TransactionError("You must supply the account UID "
                                   "for the credit account")

        if debit_account_uid == credit_account_uid:
            raise TransactionError(
                "You cannot perform a transaction where the debit and credit "
                "accounts are the same!")

        if transaction is None or transaction.is_null():
            raise TransactionError("You must supply a valid transaction to "
                                   "perform!")

        if is_provisional is None:
            raise TransactionError("You must say whether or not the "
                                   "transaction is provisional using "
                                   "is_provisional")

        if authorisation is None:
            raise PermissionError("You must supply a valid authorisation "
                                  "to perform transactions between accounts")

        authorisation.verify(account_uid=debit_account_uid)
        user_uid = authorisation.user_uid()

        # load the account from which the transaction will be performed
        bucket = login_to_service_account()
        debit_account = Account(uid=debit_account_uid, bucket=bucket)

        # validate that this account is in a group that can be authorised
        # by the user
        if not Accounts(user_uid).contains(account=debit_account,
                                           bucket=bucket):
            raise PermissionError(
                "The user with UID '%s' cannot authorise transactions from "
                "the account '%s' as they do not own this account." %
                (user_uid, str(debit_account)))

        # now load the two accounts involved in the transaction
        credit_account = Account(uid=credit_account_uid, bucket=bucket)

        # we have enough information to perform the transaction
        transaction_records = Ledger.perform(transactions=transaction,
                                             debit_account=debit_account,
                                             credit_account=credit_account,
                                             authorisation=authorisation,
                                             is_provisional=is_provisional,
                                             bucket=bucket)

        status = 0
        message = "Success"

    except Exception as e:
        error = e

    return_value = create_return_value(status, message, log, error)

    if transaction_records:
        for i in range(0, len(transaction_records)):
            transaction_records[i] = transaction_records[i].to_data()

        return_value["transaction_records"] = transaction_records

    return pack_return_value(return_value, args)


if __name__ == "__main__":
    try:
        from fdk import handle
        handle(handler)
    except Exception as e:
        print("Error running function: %s" % str(e))
        raise
