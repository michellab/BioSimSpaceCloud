

__all__ = [ "QRCodeError", "LoginError", "AccountError" ]

class QRCodeError(Exception):
    pass

class LoginError(Exception):
    pass

class AccountError(Exception):
    pass
