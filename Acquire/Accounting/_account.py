
import uuid as _uuid
from copy import copy as _copy
import datetime as _datetime
import time as _time

from Acquire.Service import login_to_service_account \
                        as _login_to_service_account
from Acquire.ObjectStore import ObjectStore as _ObjectStore

from ._errors import AccountError, InsufficientFundsError

__all__ = ["Account"]


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
           from the object store (so 'name' and 'description' should be "None")
        """
        if uid:
            self._uid = str(uid)
            self._name = None
            self._description = None
        elif not (name is None):
            self._create_account(name, description)
        else:
            self._uid = None

    def _create_account(self, name, description):
        """Create the account from scratch"""
        if name is None or description is None:
            raise AccountError(
                "You must pass both a name and description to create a new "
                "account")

        if self._uid is not None:
            raise AccountError("You cannot create an account twice!")

        self._uid = _uuid.uuid4()
        self._name = str(name)
        self._description = str(description)
        self._overdraft_limit = 0
        self._maximum_daily_limit = None

    def is_null(self):
        """Return whether or not this is a null account"""
        return self._uid is None

    def name(self):
        """Return the name of this account"""
        if self.is_null():
            return None

        return self._name

    def description(self):
        """Return the description of this account"""
        if self.is_null():
            return None

        return self._description

    def uid(self):
        """Return the UID for this account."""
        return self._uid

    def key(self):
        """Return the key for this account in the object store"""
        if self.is_null():
            return None

        return "%s/%s" % (_account_root(), self.uid())

    def _load_account(self):
        """Load the current state of the account from the object store"""
        if self.is_null():
            return

        bucket = _login_to_service_account()
        data = _ObjectStore.get_object_from_json(bucket, self.key())
        self.__dict__ = _copy(Account.from_data(data).__dict__)

    def _save_account(self):
        """Save this account back to the object store"""
        bucket = _login_to_service_account()
        _ObjectStore.set_object_from_json(bucket, self.key(), self.to_data())

    def to_data(self):
        """Return a dictionary that can be encoded to json from this object"""
        data = {}

        if not self.is_null():
            data["uid"] = self._uid
            data["name"] = self._name
            data["description"] = self._description
            data["overdraft_limit"] = self._overdraft_limit
            data["maximum_daily_limit"] = self._maximum_daily_limit

        return data

    @staticmethod
    def from_data(data):
        """Construct and return an Account from the passed dictionary that has
           been decoded from json
        """
        account = Account()

        if (data and len(data) > 0):
            account._uid = data["uid"]
            account._name = data["name"]
            account._description = data["description"]
            account._overdraft_limit = data["overdraft_limit"]
            account._maximum_daily_limit = data["maximum_daily_limit"]

        return account

    def _debit(self, transaction, authorisation, bucket=None):
        """Debit the value of the passed transaction  from this account based
           on the authorisation contained
           in 'authorisation'. This will create a unique ID (UID) for
           this debit and will return this together with the timestamp of the
           debit.

           The UID will encode both the date of the debit and provide a random
           ID that together can be used to identify the transaction associated
           with this debit in the future.

           This will raise an exception if the debit cannot be completed, e.g.
           if the authorisation is invalid, if the debit exceeds a limit or
           there are insufficient funds in the account

           Note that this function is private as it should only be called
           by the DebitNote class
        """
        if self.is_null() or transaction.value() <= 0:
            return None

        # self.assert_valid_authorisation(authorisation)
        if bucket is None:
            bucket = _login_to_service_account()

        if self.available_balance(bucket) < transaction.value():
            raise InsufficientFundsError(
                "You cannot debit '%s' from account %s as there "
                "are insufficient funds in this account." %
                (transaction, str(self)))

        # create a UID and timestamp for this debit and record
        # it in the account
        now = _datetime.datetime.now()

        # don't allow any transactions in the last 30 seconds of the day, as we
        # will sum up the day balance at midnight, and don't want to risk any
        # late transactions from messing up the accounting
        while now.hour == 23 and now.minute == 59 and now.second >= 30:
            _time.sleep(5)
            now = _datetime.datetime.now()

        timestamp = now.timestamp()

        day_key = "%4d-%02d-%02d" % (now.year, now.month, now.day)

        uid = "%s/%s" % (day_key, _uuid.uuid4())

        obj_key = "%s/DR:%s" % (uid, transaction.value_string())

        # write this debit to the object store
        data = {"timestamp": timestamp,
                "uid": uid,
                "authorisation": authorisation.to_data()}

        _ObjectStore.set_object_from_json(bucket, obj_key, data)

        if self.is_beyond_overdraft_limit(bucket):
            # This transaction has helped push the account beyond the
            # overdraft limit. Delete the transaction and raise
            # an InsufficientFundsError
            _ObjectStore.delete_object(bucket, obj_key)
            raise InsufficientFundsError(
                "You cannot debit '%s' from account %s as there "
                "are insufficient funds in this account." %
                (transaction, str(self)))

        return (uid, timestamp)

    def available_balance(self, bucket=None):
        """Return the available balance of this account. This is the amount
           of value that can be spent (e.g. includes overdraft and fixed daily
           spend limits)
        """
        if self.is_null():
            return 0

        if bucket is None:
            bucket = _login_to_service_account()

        pass

    def balance(self, bucket=None):
        """Return the current balance of this account"""
        if self.is_null():
            return 0

        if bucket is None:
            bucket = _login_to_service_account()

        pass

    def overdraft_limit(self):
        """Return the overdraft limit of this account"""
        if self.is_null():
            return 0

        return self._overdraft_limit

    def is_beyond_overdraft_limit(self, bucket=None):
        """Return whether or not the current balance is beyond
           the overdraft limit
        """
        return self.balance(bucket) < -(self.overdraft_limit())
