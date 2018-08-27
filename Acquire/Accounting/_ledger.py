
from Acquire.ObjectStore import ObjectStore as _ObjectStore
from Acquire.Service import login_to_service_account as _login_to_service_account

from cachetools import cached as _cached
from cachetools import TTLCache as _TTLCache

import datetime as _datetime
import uuid as _uuid

# The cache can hold a maximum of 200 objects, and will be renewed
# every 300 seconds (so any changes in this service's key would
# cause problems for a maximum of 300 seconds)
_cache = _TTLCache(maxsize=50, ttl=300)

__all__ = ["Ledger", "LedgerAccount", "LedgerError",
           "Transaction", "TransactionCode", "TransactionError" ]

class LedgerError(Exception):
    pass

class TransactionError(Exception):
    pass

@_cached(_cache)
def _get_transaction(key):
    """Return the passed transaction. These are read only, so this
       function can be safely cached. This is stored in the object
       store at 'key'
    """
    bucket = _login_to_service_account()
    return Transaction.from_data(_ObjectStore.get_object_from_json(bucket,key))

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
        day_key = "%s/%d-%02d-%02d" % (daytime.year,daytime.month,daytime.day)
      
        entries = _ObjectStore.get_all_object_names(bucket, day_key)

        for entry in entries:
            timestamp = float( entry.split("/")[0] )

            if timestamp >= start_time and timestamp < end_time:
                transaction_keys.append( "%s/%s" % (day_key,entry) )

    transactions = []

    for key in transaction_keys:
        transactions.append( _get_transaction("%s/%s" % (ledger_key,key)) )

    return transactions

from enum import Enum as _Enum

_shortcodes = [ "??", "CR", "DR" ]

class TransactionCode(_Enum):
    NONE = 0
    CREDIT = 1
    DEBIT = 2

    def shortcode(self):
        """Return the short (2-letter) code for this type"""
        return _shortcodes(self.value)

    def to_shortcode(self):
        """Synonym for .shortcode()"""
        return self.shortcode()

    @staticmethod
    def from_shortcode(code):
        try:
            return TransactionCode(_shortcodes.index(code.upper()))
        except:
            raise TransactionError("Cannot recognise the short code '%s'" % code)

class Transaction:
    """This is an entry for a transaction in the accounting ledger. This
       records the timestamp of the entry, its type, and the
       value (always positive - the type will determine whether this
       is a debit or credit).

       Each entry has a unique ID that is used to locate
       it in the ledger, and a timestamp for when it was created
    """
    def __init__(self, value=None, code=TransactionCode.NONE, 
                 description=None, datetime=None):

        if value is None:
            return

        try:
            self._value = float(value)
        except:
            self._value = -1
        
        if self._value < 0:
            raise TransactionError("A transaction must have a numeric "
                                   "value that is >= 0 (be positive). '%s' "
                                   "is not a valid value!" % value)

        if isinstance(code,str):
            self._code = TransactionCode(code)

        elif isinstance(type,TransactionCode):
            self._code = code
        else:
            raise TransactionError("A transaction must be given a valid "
                                   "transaction type. '%s' is not valid!" % type)

        if description is None:
            self._description = None
        else:
            self._description = str(description)
        
        self._uid = _uuid.uuid4()

        if datetime:
            self._timestamp = datetime.timestamp()
        else:
            self._timestamp = _datetime.datetime.now().timestamp()        

    def code(self):
        """Return the code of this transaction (e.g. debit, credit, etc.)"""
        return self._code

    def uid(self):
        """Return the UID of this entry"""
        return self._uid

    def timestamp(self):
        """Return the timestamp of this entry"""
        return self._timestamp

    def description(self):
        """Return a description of the entry"""
        return self._description

    def value(self):
        """Return the value of the transaction."""
        return self._value

    def valueKey(self):
        """Return the value of this deposit as an object store
           key, e.g. DR:3.54135 or CR:1.33412. This will return
           the value to a maximum of 6 decimal places
        """
        return "%s:%s" % (self._code.shortcode(),
                          str(float(self._value)))

    def key(self):
        """Return a unique key that can be used to identify
           and search for this entry. The key is in the format
           year-month-day/timestamp/code/uid
        """
        timestamp = self.timestamp()
        now = _datetime.datetime.fromtimestamp(timestamp)
        return "%4d-%02d-%02d/%s/%s/%s" % (now.year,now.month,now.day,
                                          self._timestamp,self._code.shortcode(),
                                          self.uid())

    def to_data(self):
        """Return this object converted to a dictionary"""
        data = {}
        data["value"] = self._value
        data["uid"] = self._uid
        data["description"] = self._description
        data["timestamp"] = self._timestamp 
        data["code"] = self._code.shortcode()

    @staticmethod
    def from_data(data):
        """Return the object constructed from the passed data"""
        item = Transaction()

        item._value = data["value"]
        item._uid = data["uid"]
        item._description = data["description"]
        item._timestamp = data["timestamp"]
        item._code = TransactionCode(data["code"])

        return item

class LedgerAccount:
    """This class holds information about a single account in
       the ledger. Accounts are classified using the American
       system into Assets, Capital, Liabilities, Incomes 
       and Losses
    """
    def __init__(self, name=None, description=None):
        self._name = name
        self._description = description

        if self._name:
            self._name = str(self._name)
            self._uid = _uuid.uuid4()
            self._created_ordinal = _datetime.datetime.now().toordinal()

    def name(self):
        """Return the name of this account"""
        return self._name

    def description(self):
        """Return the description of this account"""
        return self._description
        
    def is_null(self):
        """Return whether or not this is a null account"""
        return self._uid is None
    
    def balance(self, date=None):
        """Return the current balance of this account. If date
           is supplied, then it returns the balance at the 
           end of day on 'date'. Otherwise it returns the 
           current balance. Note that the balance excludes
           all liabilities (meaning that the actual balance
           is the total plus the liabilities). This really
           shows how much is available to commit/spend
        """
        if self.is_null():
            return 0
    
    def liabilities(self, date=None):
        """Return the current liabilities of this account. If date
           is supplied, then it returns the liabilities at the
           end of day on 'date'. Otherwise it returns the
           current liability
        """
        if self.is_null():
            return 0
    
    def to_data(self):
        """Return this object converted to a data dictionary that
           can be seralised to json
        """
        if self.is_null():
            return None

        data = {}
        data["name"] = self._name
        data["description"] = self._description
        data["uid"] = self._uid
        data["created_ordinal"] = self._created_ordinal

        return data

    @staticmethod
    def from_data(data):
        """Return this account created from the passed decoded json dictionary"""
        if data is None:
            return LedgerAccount()
        
        l = LedgerAccount()
        
        l._name = data["name"]
        l._description = data["description"]
        l._uid = data["uid"]
        l._created_ordinal = data["created_ordinal"]

        return l

class Ledger:
    """This class holds the overall ledger (financial accounts) 
       for all users, functions, etc. for this accounting service

       The individual transactions in this ledger are stored in 
       the object store. This class is used to simplify reading
       and writing transactions, and checking balances, spending
       limits etc.
    """
    def __init__(self):
        """Construct a ledger for the passed user"""
        pass

    def ledger_key(self):
        """Return the root key for items in the ledger"""
        return "ledger/%s" % self._user_id

    @staticmethod
    def from_data(data):
        """Construct from the passed data"""
        l = Ledger()

        return l

    def to_data(self):
        """Return this object packed to a dictionary"""
        data = {}

        return data

    def get_transactions(self, start_date, end_date):
        """Return all of the transactions in the ledger"""
        return self._get_all_transactions(self.ledger_key(),
                                     start_date.timestamp(), end_date.timestamp())

    def _get_all_transactions(self, bucket, start_time, end_time):
        """Return all of the ledger transactions between start_time and end_time.
           This matches entries that are >= start_time and < end_time
        """
        return _get_all_transactions(bucket, self.ledger_key(),
                                     start_time, end_time)
