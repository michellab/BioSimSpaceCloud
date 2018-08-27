
from Acquire.Service import ServiceError

__all__ = [ "AccountingServiceError", "LedgerError", "TransactionError" ]

class AccountingServiceError(ServiceError):
    pass

class LedgerError(Exception):
    pass

class TransactionError(Exception):
    pass
