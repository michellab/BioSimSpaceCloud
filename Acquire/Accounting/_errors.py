
from Acquire.Service import ServiceError

__all__ = ["AccountingServiceError", "LedgerError", "TransactionError",
           "AccountError", "UnbalancedLedgerError", "InsufficientFundsError"]


class AccountingServiceError(ServiceError):
    pass


class AccountError(Exception):
    pass


class LedgerError(Exception):
    pass


class TransactionError(Exception):
    pass


class UnbalancedLedgerError(Exception):
    pass


class InsufficientFundsError(Exception):
    pass
