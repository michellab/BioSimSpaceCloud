
from ._account import Account as _Account

from Acquire.ObjectStore import ObjectStore as _ObjectStore
from Acquire.ObjectStore import Mutex as _Mutex
from Acquire.ObjectStore import string_to_encoded as _string_to_encoded
from Acquire.ObjectStore import encoded_to_string as _encoded_to_string

from Acquire.Service import login_to_service_account as \
                            _login_to_service_account

from ._errors import AccountError

__all__ = ["Accounts"]


class Accounts:
    """This class provides the interface to grouping and ungrouping
       accounts, and associating them with users and services
    """
    def __init__(self, group=None):
        """Construct an interface to the group of accounts called 'group'.
           If the group is not specified, then it will default to 'default'
        """
        if group is None:
            group = "default"

        self._group = str(group)

    def __str__(self):
        return "Accounts(group=%s)" % self.group()

    def _root(self):
        """Return the root key for this group in the object store"""
        return "account_groups/%s" % _string_to_encoded(self._group)

    def _account_key(self, name):
        """Return the key for the account called 'name' in this group"""
        return "%s/%s" % (self._root(),
                          _string_to_encoded(str(name)))

    def group(self):
        """Return the name of the group that this set of accounts refers to"""
        return self._group

    def list_accounts(self, bucket=None):
        """Return the names of all of the accounts in this group"""
        if bucket is None:
            bucket = _login_to_service_account()

        keys = _ObjectStore.get_all_object_names(bucket, self._root())

        accounts = []

        for key in keys:
            accounts.append(_encoded_to_string(key))

        return accounts

    def get_account(self, name, bucket=None):
        """Return the account called 'name' from this group"""
        if bucket is None:
            bucket = _login_to_service_account()

        try:
            account_uid = _ObjectStore.get_string_object(
                            bucket, self._account_key(name))
        except:
            account_uid = None

        if account_uid is None:
            raise AccountError("There is no account called '%s' in the "
                               "group '%s'" % (name, self.group()))

        return _Account(uid=account_uid, bucket=bucket)

    def create_account(self, name, description=None, bucket=None):
        """Create a new account called 'name' in this group. This will raise
           an exception if an account with this name already exists
        """
        if name is None:
            raise ValueError("You must pass a name of the new account")

        account_key = self._account_key(name)

        if bucket is None:
            bucket = _login_to_service_account()

        # make sure that no-one has created this account before
        m = _Mutex(account_key, timeout=600, lease_time=600, bucket=bucket)

        try:
            account_uid = _ObjectStore.get_string_object(bucket, account_key)
        except:
            account_uid = None

        if account_uid is not None:
            m.unlock()
            # this account already exists - just return it
            account = _Account(uid=account_uid, bucket=bucket)
            return account

        # write a temporary UID to the object store so that we
        # can ensure we are the only function to create it
        try:
            _ObjectStore.set_string_object(bucket, account_key,
                                           "under_construction")
        except:
            m.unlock()
            raise

        m.unlock()

        # ok - we are the only function creating this account. Let's try
        # to create it properly
        try:
            account = _Account(name=name, description=description,
                               bucket=bucket)
        except:
            try:
                _ObjectStore.delete_object(bucket, account_key)
            except:
                pass

            raise

        _ObjectStore.set_string_object(bucket, account_key, account.uid())

        return account
