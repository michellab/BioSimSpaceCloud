
import uuid as _uuid
from copy import copy as _copy

from Acquire.Service import login_to_service_account as _login_to_service_account
from Acquire.ObjectStore import ObjectStore as _ObjectStore

from ._errors import AccountError

__all__ = [ "Account" ]

def _account_root():
    return "accounts"

class Account:
    """This class represents a single account in the ledger. It has a balance,
       and a record of the set of transactions that have been applied.

       The account really holds two accounts: the liability account and
       actual capital account. We combine both together into a single
       account to ensure that updates occur atomically

       All data for this account is stored in the object store
    """
    def __init__(self, name=None, description=None, uid=None):
        """Construct the account. If 'uid' is specified, then load the account
           from the object store (so 'name' and 'description' should be "None").
        """
        if uid:
            self._uid = str(uid)
            self._name = None
            self._description = None
        else:
            self._create_account(name, description)

    def _create_account(self, name, description):
        """Create the account from scratch"""
        self._uid = _uuid.uuid4()
        self._name = str(name)
        self._description = str(description)

    def name(self):
        """Return the name of this account"""
        if not self._name:
            self._load_account()
        
        return self._name

    def description(self):
        """Return the description of this account"""
        if not self._description:
            self._load_account()
        
        return self._description

    def uid(self):
        """Return the UID for this account"""
        if not self._uid:
            raise AccountError("Cannot get the UID of a null account")

        return self._uid 

    def key(self):
        """Return the key for this account in the object store"""
        return "%s/%s" % (_account_root(),self.uid())

    def _load_account(self):
        """Load the current state of the account from the object store"""
        bucket = _login_to_service_account()

        data = _ObjectStore.get_object_from_json(bucket, self.key())
        self.__dict__ = _copy( Account.from_data(data).__dict__)

    def _save_account(self):
        """Save this account back to the object store"""
        bucket = _login_to_service_account()
        _ObjectStore.set_object_from_json(bucket, self.key(), self.to_data())

    def to_data(self):
        """Return a dictionary that can be encoded to json from this object"""
        data = {}

        data["uid"] = self._uid
        data["name"] = self._name
        data["description"] = self._description
    
        return data

    @staticmethod
    def from_data(data):
        """Construct and return an Account from the passed dictionary that has 
           been decoded from json
        """
        account = Account()

        account._uid = data["uid"]
        account._name = data["name"]
        account._description = data["description"]

        return account 

    def balance(self):
        """Return the current balance of this account"""
        