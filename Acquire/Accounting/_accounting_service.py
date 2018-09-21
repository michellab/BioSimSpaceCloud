
import uuid as _uuid
from copy import copy as _copy

from Acquire.Crypto import PrivateKey as _PrivateKey
from Acquire.Crypto import PublicKey as _PublicKey

from Acquire.Service import call_function as _call_function
from Acquire.Service import Service as _Service

from ._errors import AccountingServiceError

__all__ = ["AccountingService", "AccountingServiceError"]


class AccountingService(_Service):
    """This is a specialisation of Service for Accounting Services"""
    def __init__(self, other=None):
        if isinstance(other,_Service):
            self.__dict__ = _copy(other.__dict__)

            if not self.is_accounting_service():
                raise AccountingServiceError(
                    "Cannot construct an AccountingService from "
                    "a service which is not an accounting service!")
        else:
            _Service.__init__(self)

    def list_accounts(self, user):
        """Return a list of the accounts that are available for the passed
           user on this accounting service. Note that the user must have
           successfully logged in to be able to access this information
        """
        if not user.is_logged_in():
            raise PermissionError("You cannot list the accounts for user "
                                  "%s because they have not yet logged in!" %
                                  user.name())

    def get_account(self, name, user=None):
        """Return the account called 'name' that belongs to user 'user'.
           If the user is logged in, then this will return an account
           with permissions set to allow you to transfer value out
           from the account. Otherwise the returned account is read-only,
           providing only really a handle to which value can be
           transferred
        """
        return Account(name, user=user, accounting_service=self)

    def create_account(self, user, name, description=None):
        """Tell this accounting service to create a new account for the passed
           user with the account called 'name' (and optionally a
           description 'description'). This will fail if the account
           with this name for this user already exists. This returns
           the (authenticated) account
        """
        if not user.is_logged_in():
            raise PermissionError("You cannot create the account called '%s' "
                                  "for user %s because they have not yet "
                                  "logged in!" %
                                  (name, user.name()))

