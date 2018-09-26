
import json
import os
import datetime

from Acquire.Service import unpack_arguments, get_service_private_key, \
                            get_trusted_service_info, login_to_service_account
from Acquire.Service import create_return_value, pack_return_value

from Acquire.Accounting import Account, Accounts, Authorisation, \
                               Transaction, Ledger


class TransactionError(Exception):
    pass


def handler(ctx, data=None, loop=None):
    """This function is called to handle requests from a user to deposit
       more funds into their account. This will add this deposit as a
       debt for the user. Once the debt exceeds a certain value, then the
       backend-payment system will charge the user's real account to
       recover the funds
    """

    status = 0
    message = None
    error = None

    log = []

    args = unpack_arguments(data, get_service_private_key)

    transaction_records = None
    invoice_value = None
    invoice_user = None

    try:
        try:
            authorisation = Authorisation.from_data(args["authorisation"])
        except:
            authorisation = None

        try:
            transaction = Transaction.from_data(args["transaction"])
        except:
            try:
                transaction = Transaction(
                                args["deposit"],
                                "Deposit on %s" % datetime.datetime.now())
            except:
                transaction = None

        if authorisation is None:
            raise PermissionError("You must supply a valid authorisation "
                                  "to deposit funds into your account")

        authorisation.verify()
        user_uid = authorisation.user_uid()

        # load the account from which the transaction will be performed
        bucket = login_to_service_account()
        accounts = Accounts(user_uid)

        # deposits are made by transferring funds from the user's
        # 'billing' account to their 'deposits' account.
        deposit_account = accounts.create_account(
                            "deposits", "Deposit account",
                            bucket=bucket)

        billing_account = accounts.create_account(
                            "billing", "Billing account",
                            overdraft_limit=150, bucket=bucket)

        billing_balance = billing_account.balance() - transaction.value()

        if billing_balance < -50.0:
            # there are sufficient funds that need to be transferred that
            # it is worth really charging the user
            invoice_user = user_uid
            invoice_value = billing_balance

        # we have enough information to perform the transaction
        transaction_records = Ledger.perform(transactions=transaction,
                                             debit_account=billing_account,
                                             credit_account=deposit_account,
                                             authorisation=authorisation,
                                             is_provisional=False,
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

    if invoice_user:
        return_value["invoice_user"] = invoice_user
        return_value["invoice_value"] = str(invoice_value)

    return pack_return_value(return_value, args)


if __name__ == "__main__":
    try:
        from fdk import handle
        handle(handler)
    except Exception as e:
        print("Error running function: %s" % str(e))
        raise
