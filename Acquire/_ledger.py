
from ._objstore import ObjectStore as _ObjectStore
from ._login_to_objstore import login_to_service_account as _login_to_service_account

from cachetools import cached as _cached
from cachetools import TTLCache as _TTLCache

# The cache can hold a maximum of 200 objects, and will be renewed
# every 300 seconds (so any changes in this service's key would
# cause problems for a maximum of 300 seconds)
_cache = _TTLCache(maxsize=50, ttl=300)

__all__ = ["Ledger", "LedgerEntry" ]

class LedgerError(Exception):
    pass

@_cached(_cache)
def _get_ledger_entry(entry):
    """Return the passed ledger entry. These are read only, so this
       function can be safely cached
    """
    bucket = _login_to_service_account()
    return LedgerEntry.from_data(_ObjectStore.get_object_from_json(bucket,entry))

def _get_ordinal(timestamp):
    """Return the ordinal day from the passed timestamp"""
    return _datetime.datetime.fromtimestamp(timestamp).toordinal()

def _get_all_ledger_entries(ledger_key, start_time, end_time):
    """Return all of the ledger entries entered at the passed key"""

    if start_time >= end_time:
        return []

    bucket = _login_to_service_account()

    start_day = _get_ordinal(start_time)
    end_day = _get_ordinal(end_time)

    ledger_entries = []

    for day in range(start_day, end_day+1):
        daytime = _datetime.datetime.fromordinal(day)
        day_key = "%s/%d-%02d-%02d" % (ledger_keyday.year,day.month,day.day)
      
        entries = _ObjectStore.get_all_object_names(bucket, day_key)

        for entry in entries:
            timestamp = float( entry.split("/")[0] )

            if timestamp >= start_time and timestamp < end_time:
                ledger_entries.append( "%s/%s" % (day_key,entry) )

    ledger_entries = _ObjectStore.get_all_object_names(bucket, ledger_key)

    entries = []

    for entry in ledger_entries:
        entries.append( _get_ledger_entry("%s/%s" % (ledger_key,entry)) )

    return entries

class LedgerEntry:
    """This is an entry in the accounting ledger. This
       records the timestamp of the entry and the
       value (negative for debit, positive for credit).
       Each entry has a unique ID that is used to locate
       it in the ledger
    """
    def __init__(self, value=0, description=None, now=None):
        self._value = float(value)

        if not description is None:
            self._description = str(description)

        self._uid = None
        self._timestamp = None

        if now:
            self._timestamp = now.timestamp()

    def uid(self):
        """Return the UID of this entry"""
        if self._uid is None:
            self._uid = str(_uuid.uuid4())

        return self._uid

    def timestamp(self):
        """Return the timestamp of this entry"""
        if self._timestamp is None:
            self._timestamp = _datetime.datetime.now().timestamp()

        return self._timestamp

    def description(self):
        """Return a description of the entry"""
        return self._description

    def value(self):
        """Return the value of the transaction. Positive values
           are credits and negative values are debits
        """
        return self._value

    def mirror(self):
        """Return the double-entry mirror of this item (the item
           with the negative of this value, i.e. the corresponding
           credit to this debit, or debit to this credit
        """
        item = LedgerItem()
        item._description = self._description
        item._value = -(self._value)
        item._uid = self._uid
        item._timestamp = self._timestamp

        return item

    def key(self):
        """Return a unique key that can be used to identify
           and search for this entry. The key is in the format
           year-month-day/timestamp/uid
        """
        timestamp = self.timestamp()
        now = _datetime.datetime.fromtimestamp(timestamp)
        return "%d-%02d-%02d/%s/%s" % (now.year,now.month,now.day,
                                                self._timestamp,self.uid())

    def to_data(self):
        """Return this object converted to a dictionary"""
        data = {}
        data["value"] = self._value
        data["uid"] = self._uid
        data["description"] = self._description
        data["timestamp"] = self._timestamp 

    @staticmethod
    def from_data(data):
        """Return the object constructed from the passed data"""
        item = LedgerItem()

        item._value = data["value"]
        item._uid = data["uid"]
        item._description = data["description"]
        item._timestamp = data["timestamp"]

        return item

class Ledger:
    """This class holds a ledger for a user. This holds the
       details about the account that owns this ledger, plus
       limits for spending etc.
    """
    def __init__(self, username=None, user_uid=None, identity_service=None):
        """Construct a ledger for the passed user"""
        self._username = username
        self._user_uid = user_uid
        self._identity_service = identity_service
        self._clear_budget_cache()

    def ledger_key(self):
        """Return the root key for items in the ledger"""
        return "ledger/%s" % self._user_id

    @staticmethod
    def from_data(data):
        """Construct from the passed data"""
        l = Ledger()

        l._username = data["username"]
        l._user_uid = data["user_uid"]
        l._identity_service = identity_service

        return l

    def to_data(self):
        """Return this object packed to a dictionary"""
        data = {}

        data["username"] = self._username
        data["user_uid"] = self._user_uid
        data["identity_service"] = self._identity_service

        return data

    def get_entries(self, start_date, end_date):
        """Return all of the entries in the ledger"""
        return self._get_all_entries(self.ledger_key(),
                                     start_date.timestamp(), end_data.timestamp())

    def _get_all_entries(self, bucket, start_time, end_time):
        """Return all of the ledger entries between start_time and end_time.
           This matches entries that are >= start_time and < end_time"""
        entries = []

        entries = _get_all_ledger_entries(bucket, "%s/liabilities" % self.ledger_key(),
                                          start_time, end_time)

        entries += _get_all_ledger_entries(bucket, "%s/debits" % self.ledger_key(),
                                           start_time, end_time)

        entries += _get_all_ledger_entries(bucket, "%s/credits" % self.ledger_key(),
                                           start_time, end_time)

        return entries

    def _get_todays_starting_balance(self, bucket, now):
        """Return the balance of the account (including outstanding
           liabilities) at the start of today
        """
        today = _datetime.datetime.fromordinal( now.toordinal() )

        key = "%s/balance/%d-%02d-%02d" % (self.ledger_key(),
                                           today.year,today.month,today.day)

        balance = _ObjectStore.get_string_object(bucket, key)

        if balance is None:
            yesterday = _datetime.datetime.fromordinal( today.toordinal() - 1 )

            yesterdays_starting_balance = \
                        self._get_todays_starting_balance(bucket, yesterday)

            # now sum up all of yesterday's commitments
            start_today = _datetime.datetime
            entries = self._get_all_entries(bucket, yesterday, today)

            yesterdays_spend = 0

            for entry in entries:
                 yesterdays_spend += entry.value()

            todays_starting_balance = yesterdays_starting_balance - yesterdays_spend

            _ObjectStore.set_string_object(bucket, key, str(todays_starting_balance))

            balance = todays_starting_balance

        return float(balance)

    def _clear_budget_cache(self):
        """Internal function that resets the budget cache,
           so that we have to recalculate it from the ledger
           items from scratch
        """
        self._daily_spend = 0
        self._last_update = None

    def _get_account_balance(self, bucket):
        """Internal function that sums through the ledger to 
           calculate the balance on the account (including
           outstanding liabilities) and returns the spend for
           today as well as the total balance
        """
        now = _datetime.datetime().now()
        timestamp = now.timestamp()

        starting_balance = self._get_todays_starting_balance(bucket, now)
        daily_spend = self._daily_spend

        # get all updates between last_timestamp and this timestamp
        entries = self._get_all_entries(bucket, self._last_update, timestamp)

        for entry in entries:
            daily_spend += entry.value()

        self._last_update = timestamp
        self._daily_spend = daily_spend

        return (daily_spend, todays_balance-daily_spend)

    def add_liability(self, description, value):
        """Add the passed item as a liability in the ledger. This
           will only be added if the current spend (including current
           daily liability) is below the daily spend limit,
           and there is sufficient credit in the account. This
           will return the LedgerEntry if succesful, or will raise
           an exception to signify why the liability cannot be
           held. We expect you to either cancel the liability or
           receipt the liability at some point in the future...
        """

        description = str(description)
        value = float(value)

        if value < 0:
            raise LedgerError("You cannot have an item with a negative cost! %s" % \
                                  value )

        bucket = _login_to_identity_account()

        daily_cap = self.daily_cap()
        (total_spend_today, account_balance) = self._get_account_balance(bucket)

        if account_balance - value < 0:
            raise InsuffientFundsError("You do not have sufficient credit "
                    "to fund '%s'. Please credit at least '%s'." % \
                        (description,(value-account_balance)))

        if total_spend_today + value > daily_cap:
            raise CostBreaksCapError("The cost of '%s' (%s) will break "
                    "your daily cap. You need to increase the cap or "
                    "wait until tomorrow" % (description,value,daily_cap))

        # create a LedgerEntry and write it to the object store
        now = _datetime.datetime.now()

        # if we are within 5 seconds of midnight then wait until after 
        # midnight, so that we don't cause problems by writing an entry
        # after the total for the day has been calculated
        while (now.hour == 23 and now.minute == 59 and now.second >= 55):
            _time.sleep(1)
            now = _datetime.datetime.now()

        entry = LedgerEntry(description, value, now)

        entry_key = "%s/liabilities/%s" % (self.ledger_key(),entry.key())
        _ObjectStore.set_object_from_json(bucket, entry_key, entry.to_data())

        # while we were writing someone else could have beaten us to 
        # writing a liability. Check that the balance and daily caps are ok
        (total_spend_today, account_balance) = self._get_account_balance(bucket)

        if total_spend_today <= daily_cap and account_balance >= 0:
            # everything is ok :-)
            return entry

        # we have double-spent some money... reject this transaction
        _ObjectStore.delete_object(bucket, entry_key)
        self._clear_budget_cache()

        if account_balance < 0:
            raise InsuffientFundsError("You do not have sufficient credit "
                    "to fund '%s'. Please credit at least '%s'." % \
                        (description,(value-account_balance)))

        if total_spend_today > daily_cap:
            raise CostBreaksCapError("The cost of '%s' (%s) will break "   
                    "your daily cap. You need to increase the cap or "
                    "wait until tomorrow" % (description,value,daily_cap)) 
