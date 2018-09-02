
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

__all__ = ["Account", "LineItem", "Authorisation"]


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
       basic information about the item, e.g. its UID and authorisation
    """
    def __init__(self, uid=None, authorisation=None):
        self._uid = uid
        self._authorisation = authorisation

    def is_null(self):
        """Return whether or not this is a null line item"""
        return self._uid is None

    def uid(self):
        """Return the UID of the TransactionRecord that provides
           more information about this line item in the ledger
        """
        return self._uid

    def authorisation(self):
        """Return the authorisation that was used to authorise this action"""
        return self._authorisation

    def to_data(self):
        """Return this object as a dictionary that can be serialised to json"""
        data = {}

        if not self.is_null():
            data["uid"] = self._uid
            data["authorisation"] = self._authorisation

        return data

    @staticmethod
    def from_data(data):
        """Return a LineItem constructed from the json-decoded dictionary"""
        l = LineItem()

        if (data and len(data) > 0):
            l._uid = data["uid"]
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
        self._maximum_daily_limit = 0

        # initialise the account with a balance of zero
        bucket = _login_to_service_account()
        self._record_daily_balance(0, 0, 0, bucket=bucket)
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

        return _get_key_from_day("%s/balance" % self._key(),
                                 datetime)

    def _record_daily_balance(self, balance, liability, receivable,
                              datetime=None, bucket=None):
        """Record the starting balance for the day containing 'datetime'
           as 'balance' with the starting outstanding liabilities at
           'liability' and starting outstanding accounts receivable at
           'receivable' If 'datetime' is none, then the balance
           for today is set.
        """
        if self.is_null():
            return

        if datetime is None:
            datetime = _datetime.datetime.now()

        balance = _create_decimal(balance)
        liability = _create_decimal(liability)
        receivable = _create_decimal(receivable)

        balance_key = self._get_balance_key(datetime)

        if bucket is None:
            bucket = _login_to_service_account()

        data = {"balance": str(balance),
                "liability": str(liability),
                "receivable": str(receivable)}

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
                        bucket, "%s/balance" % self._key())

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
           returns a tuple of
           (balance, liability, receivable).

           where 'balance' is the current real balance of the account,
           neglecting any outstanding liabilities or accounts receivable,
           where 'liability' is the current total liabilities,
           where 'receivable' is the current total accounts receivable, and

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
                _Decimal(data["liability"]),
                _Decimal(data["receivable"]))

    def _get_balance(self, bucket=None, datetime=None):
        """Get the balance of the account for the passed datetime. This
           returns a tuple of

           (balance, liability, receivable)

           where 'balance' is the current real balance of the account,
           neglecting any outstanding liabilities or accounts receivable,
           where 'liability' is the current total liabilities,
           where 'receivable' is the current total accounts receivable

           If datetime is None then the balance "now" is returned
        """
        if datetime is None:
            return self._get_current_balance(bucket)

        raise NotImplementedError("NOT IMPLEMENTED!")

    def _recalculate_current_balance(self, bucket, now):
        """Internal function that implements _get_current_balance
           by recalculating the total from today from scratch
        """
        # where were we at the start of today?
        (balance, liability, receivable) = self._get_daily_balance(bucket, now)

        # now sum up all of the transactions from today
        transaction_keys = self._get_transaction_keys_between(
                            _datetime.datetime.fromordinal(now.toordinal),
                            now)

        # summing transactions...
        # DR - DEBIT, CR - CREDIT,
        # CL - CURRENT LIABILITY, AR - ACCOUNT RECEIVABLE

        spent_today = _create_decimal(0)

        result = (balance, liability, receivable, spent_today)

        self._last_update_ordinal = now.toordinal()
        self._last_update_timestamp = now.timestamp()
        self._last_update = result

        return result

    def _update_current_balance(self, bucket, now):
        """Internal function that implements _get_current_balance
           by updating the balance etc. from transactions that have
           occurred since the last update
        """
        (balance, liability, receivable, spent_today) = self._last_update

        # now sum up all of the transactions since the last update
        transaction_keys = self._get_transaction_keys_between(
                                            self._last_update_timestamp,
                                            now)

        # summing transactions

        result = (balance, liability, receivable, spent_today)

        self._last_update_ordinal = now.toordinal()
        self._last_update_timestamp = now.timestamp()
        self._last_update = result

        return result

    def _get_current_balance(self, bucket=None):
        """Get the balance of the account now (the current balance). This
           returns a tuple of
           (balance, liability, receivable, spent_today).

           where 'balance' is the current real balance of the account,
           neglecting any outstanding liabilities or accounts receivable,
           where 'liability' is the current total liabilities,
           where 'receivable' is the current total accounts receivable, and
           where 'spent_today' is how much has been spent today (from midnight
           until now)
        """
        if bucket is None:
            bucket = _login_to_service_account()

        now = _datetime.datetime.now()
        now_ordinal = now.toordinal()
        now_timestamp = now.timestamp()

        if self._last_update_ordinal != now_ordinal:
            # we are on a new day since the last update, so recalculate
            # the balance from scratch
            return self._recalculate_current_balance(bucket, now)
        else:
            # we have calculated the total before today. Get the transactions
            # since the last update and use these to update the daily spend
            # etc.
            return self._update_current_balance(bucket, now)

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

    def _key(self):
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

        data = _ObjectStore.get_object_from_json(bucket, self._key())
        self.__dict__ = _copy(Account.from_data(data).__dict__)

    def _save_account(self, bucket=None):
        """Save this account back to the object store"""
        if bucket is None:
            bucket = _login_to_service_account()
        _ObjectStore.set_object_from_json(bucket, self._key(), self.to_data())

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

    def _credit(self, debit_note, bucket=None):
        """Credit the value in 'debit_note' to this account. If the debit_note
           shows that the payment is provisional then this will be recorded
           as accounts receivable. This will record the credit with the
           same UID as the debit identified in the debit_note, so that
           we can reconcile all credits against matching debits.
        """
        raise NotImplemented()

    def _debit(self, transaction, authorisation, is_provisional, bucket=None):
        """Debit the value of the passed transaction from this account based
           on the authorisation contained
           in 'authorisation'. This will create a unique ID (UID) for
           this debit and will return this together with the timestamp of the
           debit. If this transaction 'is_provisional' then it will be
           recorded as a liability.

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
        # up from the date and timestamp of the debit and a random string
        day_key = "%4d-%02d-%02d/%s" % (now.year, now.month, now.day,
                                        timestamp)
        uid = "%s/%s" % (day_key, _uuid.uuid4()[0:8])

        # the key in the object store is a combination of the key for this
        # account plus the uid for the debit plus the actual debit value.
        # We record the debit value in the key so that we can accumulate
        # the balance from just the key names
        if is_provisional:
            code = "CL"
        else:
            code = "DR"

        item_key = "%s/%s/%s:%s" % (self._key(), uid, code,
                                    transaction.value_string())

        # create a line_item for this debit and save it to the object store
        line_item = LineItem(uid, authorisation)

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
           spend limits, and except any outstanding liabilities)
        """
        (balance, liabilities, receivables, spent_today) \
                                     = self._get_current_balance(bucket)

        available = balance - liabilities

        if self._maximum_daily_limit:
            return min(available, self._maximum_daily_limit - spent_today)
        else:
            return available

    def balance(self, bucket=None):
        """Return the current balance of this account"""
        result = self._get_current_balance(bucket)
        return result[0]

    def liability(self, bucket=None):
        """Return the current total liability of this account"""
        result = self._get_current_balance(bucket)
        return result[1]

    def receivable(self, bucket=None):
        """Return the current total accounts receivable of this account"""
        result = self._get_current_balance(bucket)
        return result[2]

    def spent_today(self, bucket=None):
        """Return the current amount spent today on this account"""
        result = self._get_current_balance(bucket)
        return result[3]

    def overdraft_limit(self):
        """Return the overdraft limit of this account"""
        if self.is_null():
            return 0

        return self._overdraft_limit

    def is_beyond_overdraft_limit(self, bucket=None):
        """Return whether or not the current balance is beyond
           the overdraft limit
        """
        result = self._get_current_balance(bucket)

        return (result[0] - result[1]) < -(self.overdraft_limit())
