
from Acquire.Crypto import PrivateKey as _PrivateKey
from Acquire.Service import call_function as _call_function
from Acquire.Service import Service as _Service

from ._errors import LoginError

__all__ = ["Account"]


def _get_accounting_url():
    """Function to discover and return the default accounting url"""
    return "http://130.61.60.88:8080/r/accounting"


def _get_accounting_service(accounting_url=None):
    """Function to return the accounting service for the system"""
    if accounting_url is None:
        accounting_url = _get_accounting_url()

    privkey = _PrivateKey()
    response = _call_function(accounting_url, {}, response_key=privkey)

    try:
        service = _Service.from_data(response["service_info"])
    except:
        raise LoginError("Have not received the identity service info from "
                         "the identity service at '%s' - got '%s'" %
                         (accounting_url, response))

    if not service.is_accounting_service():
        raise LoginError(
            "You can only use a valid accounting service to get account info! "
            "The service at '%s' is a '%s'" %
            (accounting_url, service.service_type()))

    return service


def list_accounts(user, accounting_url=None):
    """Return the list of accounts for the passed user"""
    service = _get_accounting_service(accounting_url)

    return service.list_accounts(user)


class Account:
    """This is the client-side handle that is used to interact with
       an account on the service. If the account is created with a valid
       user login then you can perform tasks such as making payments,
       or issueing receipts or refunds. Otherwise, this is a simple
       interface that allows the account to be used as a receiver
       of value
    """
    def __init__(self, name, user=None, accounting_service=None,
                 accounting_url=None):
        """Construct the Account with the passed name, which is owned
           by the passed user
        """
        self._name = name
        self._user = user

        if accounting_service is None:
            accounting_service = _get_accounting_service(accounting_url)

        self._accounting_service = accounting_service

        self._uid = accounting_service.get_account_uid(user.name(),
                                                       name)

    def is_logged_in(self):
        """Return whether or not the user has an authenticated login
           to this account
        """
        try:
            return self._user.is_logged_in()
        except:
            return False

    def perform(self, transaction, account, is_provisional=False):
        """Tell this accounting service to apply the transfer described
           in 'transaction' from this account to 'account'. Note that
           the user must have logged into this account so that they
           have authorised this transaction. This returns the record
           of this transaction
        """
        if not self.is_logged_in():
            raise PermissionError("You cannot transfer value from '%s' to "
                                  "'%s' because you have not authenticated "
                                  "the user who owns this account" %
                                  (str(self), str(account2)))

    def receipt(self, credit_note):
        """Receipt the passed credit note that contains a request to
           transfer value from another account to the passed account
        """
        if not self.is_logged_in():
            raise PermissionError("You cannot receipt a credit note as the "
                                  "user has not yet logged in!")

    def refund(self, credit_note):
        """Refunds the passed credit note that contained a transfer of
           from another account to the passed account
        """
        if not self.is_logged_in():
            raise PermissionError("You cannot refund a credit note as the "
                                  "user has not yet logged in!")
