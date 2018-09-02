
import uuid as _uuid
from copy import copy as _copy
import datetime as _datetime
import time as _time
import re as _re

from decimal import Decimal as _Decimal
from decimal import Context as _Context

from Acquire.Service import login_to_service_account \
                        as _login_to_service_account
from Acquire.ObjectStore import ObjectStore as _ObjectStore

from ._transaction import Transaction as _Transaction
from ._errors import AccountError, InsufficientFundsError

__all__ = ["Account", "LineItem"]


def _account_root():
    return "accounts"


def _getcontext():
    """Return the context used for all decimals in transactions. This
       context rounds to 6 decimal places and provides sufficient precision
       to support any value between 0 and 999,999,999,999,999.999,999,999
       (i.e. everything up to just under one quadrillion - I doubt we will
        ever have an account that has more than a trillion units in it!)
    """
    return _Context(prec=24)


def _create_decimal(value):
    """Create a decimal from the passed value. This is a decimal that
       has 6 decimal places and is clamped between
       -1 quadrillion < value < 1 quadrillion
    """
    d = _Decimal("%.6f" % value, _getcontext())

    if d <= -1000000000000:
        raise AccountError(
                "You cannot create a balance with a value less than "
                "-1 quadrillion! (%s)" % (value))

    elif d >= 1000000000000000:
        raise AccountError(
                "You cannot create a balance with a value greater than "
                "1 quadrillion! (%s)" % (value))

    return d


def _get_key_from_day(start, datetime):
    """Return a key encoding the passed date, starting the key with 'start'"""
    return "%s/%4d-%02d-%02d" % (start, datetime.year,
                                 datetime.month, datetime.day)


def _get_day_from_key(key):
    """Return the date that is encoded in the passed key"""
    m = _re.search(r"/(\d\d\d\d)-(\d\d)-(\d\d)", key)

    if m:
        return _datetime.datetime(year=int(m.groups()[0]),
                                  month=int(m.groups()[1]),
                                  day=int(m.groups()[2]))
    else:
        raise AccountError("Could not find a date in the key '%s'" % key)


class Authorisation:
    """This class holds the information needed to authorise a transaction
       in an account
    """
    pass


class LineItem:
    """This class holds the data for a line item in the account. This holds
       basic information about the item, e.g. its UID, timestamp,
       authorisation etc.
    """
    def __init__(self, uid=None, timestamp=None, authorisation=None):
        self._uid = uid
        self._timestamp = timestamp
        self._authorisation = authorisation

    def is_null(self):
        """Return whether or not this is a null line item"""
        return self._uid is None

    def to_data(self):
        """Return this object as a dictionary that can be serialised to json"""
        data = {}

        if not self.is_null():
            data["uid"] = self._uid
            data["timestamp"] = self._timestamp
            data["authorisation"] = self._authorisation

        return data

    @staticmethod
    def from_data(data):
        """Return a LineItem constructed from the json-decoded dictionary"""
        l = LineItem()

        if (data and len(data) > 0):
            l._uid = data["uid"]
            l._timestamp = data["timestamp"]
            l._authorisation = data["authorisation"]

        return l


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
        if uid is not None:
            self._uid = str(uid)
            self._name = None
            self._description = None
            self._load_account()

            if name:
                if name != self.name():
                    raise AccountError(
                        "This account name '%s' does not match what you "
                        "expect! '%s'" % (self.name(), name))

            if description:
                if description != self.description():
                    raise AccountError(
                        "This account description '%s' does not match what "
                        "you expect! '%s'" % (self.description(), description))

        elif name is not None:
            self._uid = None
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

        self._uid = str(_uuid.uuid4())
        self._name = str(name)
        self._description = str(description)
        self._overdraft_limit = 0
        self._maximum_daily_limit = None

        # initialise the account with a balance of zero
        bucket = _login_to_service_account()
        self._record_daily_balance(0, 0, bucket)
        # make sure that this is saved to the object store
        self._save_account(bucket)

    def _get_balance_key(self, datetime=None):
        """Return the balance key for the passed time. This is the key
           into the object store of the object that holds the starting
           balance for the account on the day of the passed datetime.
           If datetime is None, then today's key is returned
        """
        if self.is_null():
            return None

        if datetime is None:
            datetime = _datetime.datetime.now()

        return _get_key_from_day("%s/balance" % self.key(),
                                 datetime)

    def _record_daily_balance(self, credit_balance, outstanding_liabilities,
                              datetime=None, bucket=None):
        """Record the starting balance for the day containing 'datetime'
           as 'credit_balance' with the starting outstanding liabilities at
           'outstanding_liabilities'. If 'datetime' is none, then the balance
           for today is set.
        """
        if self.is_null():
            return

        if datetime is None:
            datetime = _datetime.datetime.now()

        credit_balance = _create_decimal(credit_balance)
        outstanding_liabilities = _create_decimal(outstanding_liabilities)

        balance_key = self._get_balance_key(datetime)

        if bucket is None:
            bucket = _login_to_service_account()

        data = {"balance": str(credit_balance),
                "liability": str(outstanding_liabilities)}

        _ObjectStore.set_object_from_json(bucket, balance_key, data)

    def _reconcile_daily_accounts(self, bucket=None):
        """Internal function used to reconcile the daily accounts.
           This ensures that every line item transaction is summed up
           so that the starting balance for each day is recorded into
           the object store
        """
        if self.is_null():
            return

        if bucket is None:
            bucket = _login_to_service_account()

        # work back from today to the first day of the account to calculate
        # all of the daily balances... We need to record every day of the
        # account to support quick lookups
        today = _datetime.datetime.now().toordinal()
        day = today
        last_data = None
        num_missing_days = 0

        while last_data is None:
            daytime = _datetime.datetime.fromordinal(day)
            key = self._get_balance_key(daytime)
            last_data = _ObjectStore.get_object_from_json(bucket, key)

            if last_data is None:
                day -= 1
                num_missing_days += 1

                if num_missing_days > 100:
                    # we need another strategy to find the last balance
                    break

        if last_data is None:
            # find the latest day by reading the keys in the object
            # store directly
            keys = _ObjectStore.get_all_object_names(
                        bucket, "%s/balance" % self.key())

            if keys is None or len(keys) == 0:
                raise AccountError(
                    "There is no daily balance recorded for "
                    "the account with UID %s" % self.uid())

            # the encoding of the keys is such that, when sorted, the
            # last key must be the latest balance
            keys.sort()

            last_data = _ObjectStore.get_object_from_json(bucket, keys[-1])
            day = _get_day_from_key(keys[-1]).toordinal()

        # ok, now we go from the last day until today and sum up the
        # transactions from each day to create the daily balances...
        raise NotImplementedError(
                    "WILL NEED TO SUM UP INTERACTIONS FROM "
                    "%s until %s" % (_datetime.datetime.fromordinal(day)),
                    _datetime.datetime.fromordinal(today))

    def _get_daily_balance(self, bucket=None, datetime=None):
        """Get the daily starting balance for the passed datetime. This
           returns a tuple of (credit_balance,outstanding_liabilities).
           If datetime is None then todays daily balance is returned. The
           daily balance is the balance at the start of the day. The
           actual balance at a particular time will be this starting
           balance plus/minus all of the transactions between the start
           of that day and the specified datetime
        """
        if self.is_null():
            return

        if bucket is None:
            bucket = _login_to_service_account()

        if datetime is None:
            datetime = _datetime.datetime.now()

        balance_key = self._get_balance_key(datetime)

        data = _ObjectStore.get_object_from_json(bucket, balance_key)

        if data is None:
            # there is no balance for this day. This means that we haven'y
            # yet calculated that day's balance. Do the accounting necessary
            # to construct that day's starting balance
            self._reconcile_daily_accounts(bucket)

        data = _ObjectStore.get_object_from_json(bucket, balance_key)

        if data is None:
            raise AccountError("The daily balance for account at date %s "
                               "is not available" % str(datetime))

        return (_Decimal(data["balance"]),
                _Decimal(data["liability"]))

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

    def _load_account(self, bucket=None):
        """Load the current state of the account from the object store"""
        if self.is_null():
            return

        if bucket is None:
            bucket = _login_to_service_account()

        data = _ObjectStore.get_object_from_json(bucket, self.key())
        self.__dict__ = _copy(Account.from_data(data).__dict__)

    def _save_account(self, bucket=None):
        """Save this account back to the object store"""
        if bucket is None:
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

    def assert_valid_authorisation(self, authorisation):
        """Assert that the passed authorisation is valid for this
           account
        """
        if not isinstance(authorisation, Authorisation):
            raise TypeError("The passed authorisation must be an "
                            "Authorisation")

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

        if not isinstance(transaction, _Transaction):
            raise TypeError("The passed transaction must be a Transaction!")

        self.assert_valid_authorisation(authorisation)

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

        # we need to record the exact timestamp of this debit...
        timestamp = now.timestamp()

        # and to create a key to find this debit later. The key is made
        # up from the date of the debit and a random string
        day_key = "%4d-%02d-%02d" % (now.year, now.month, now.day)
        uid = "%s/%s" % (day_key, _uuid.uuid4())

        # the key in the object store is a combination of the key for this
        # account plus the uid for the debit plus the actual debit value.
        # We record the debit value in the key so that we can accumulate
        # the balance from just the key names
        item_key = "%s/%s/DR:%s" % (self.key(), uid,
                                    transaction.value_string())

        # create a line_item for this debit and save it to the object store
        line_item = LineItem(uid, timestamp, authorisation)

        _ObjectStore.set_object_from_json(bucket, item_key,
                                          line_item.to_data())

        if self.is_beyond_overdraft_limit(bucket):
            # This transaction has helped push the account beyond the
            # overdraft limit. Delete the transaction and raise
            # an InsufficientFundsError
            _ObjectStore.delete_object(bucket, item_key)
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

        (balance, liability) = self._get_daily_balance(bucket)

        return balance - liability

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
