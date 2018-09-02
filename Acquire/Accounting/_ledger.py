
from cachetools import cached as _cached
from cachetools import TTLCache as _TTLCache

import datetime as _datetime
import uuid as _uuid

from Acquire.ObjectStore import ObjectStore as _ObjectStore
from Acquire.Service import login_to_service_account as \
                            _login_to_service_account

from ._transaction import Transaction as _Transaction
from ._account import Account as _Account

from ._errors import LedgerError, TransactionError

# The cache can hold a maximum of 200 objects, and will be renewed
# every 300 seconds (so any changes in this service's key would
# cause problems for a maximum of 300 seconds)
_cache = _TTLCache(maxsize=50, ttl=300)


__all__ = ["Ledger"]


@_cached(_cache)
def _get_transaction(key):
    """Return the passed transaction. These are read only, so this
       function can be safely cached. This is stored in the object
       store at 'key'
    """
    bucket = _login_to_service_account()
    return _Transaction.from_data(
                _ObjectStore.get_object_from_json(bucket, key))


def _get_ordinal(timestamp):
    """Return the ordinal day from the passed timestamp"""
    return _datetime.datetime.fromtimestamp(timestamp).toordinal()


def _get_all_transactions(ledger_key, start_time, end_time):
    """Return all of the transactions recorded in the ledger
       between 'start_time'<= entry < end_time
    """

    if start_time >= end_time:
        return []

    bucket = _login_to_service_account()

    start_day = _get_ordinal(start_time)
    end_day = _get_ordinal(end_time)

    transaction_keys = []

    for day in range(start_day, end_day+1):
        daytime = _datetime.datetime.fromordinal(day)
        day_key = "%s/%d-%02d-%02d" % (ledger_key, daytime.year,
                                       daytime.month, daytime.day)

        entries = _ObjectStore.get_all_object_names(bucket, day_key)

        for entry in entries:
            timestamp = float(entry.split("/")[0])

            if timestamp >= start_time and timestamp < end_time:
                transaction_keys.append("%s/%s" % (day_key, entry))

    transactions = []

    for key in transaction_keys:
        transactions.append(_get_transaction("%s/%s" % (ledger_key, key)))

    return transactions


class Ledger:
    """This class holds the overall ledger (financial accounts)
       for all users, functions, etc. for this accounting service

       The individual transactions in this ledger are stored in
       the object store. This class is used to simplify reading
       and writing transactions, and checking balances, spending
       limits etc.
    """
    @staticmethod
    def _ledger_key(self):
        """Return the root key for items in the ledger"""
        return "ledger"

    @staticmethod
    def _get_all_transactions(bucket, start_time, end_time):
        """Return all of the ledger transactions between start_time
           and end_time. This matches entries that are >= start_time
           and < end_time
        """
        if isinstance(start_time, _datetime.datetime):
            start_time = start_time.timestamp()

        if isinstance(end_time, _datetime.datetime):
            end_time = end_time.timestamp()

        return _get_all_transactions(Ledger._ledger_key(),
                                     start_time, end_time)

    @staticmethod
    def get_transactions(self, start_date, end_date):
        """Return all of the transactions in the ledger"""
        return self._get_all_transactions(
                                self.ledger_key(),
                                start_date.timestamp(),
                                end_date.timestamp())
