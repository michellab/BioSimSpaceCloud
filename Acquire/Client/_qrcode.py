
# If we can, import qrcode to auto-generate QR codes
# for the login url
try:
    import qrcode as _qrcode
    _has_qrcode = True
except:
    _has_qrcode = False

from ._errors import QRCodeError

__all__ = [ "create_qrcode", "has_qrcode" ]

def has_qrcode():
    """Return whether or not we support creating QR codes"""
    return _has_qrcode

def create_qrcode(uri):
    """Return a QR code for the passed URI"""
    if not _has_qrcode:
        raise QRCodeError("Cannot find the qrcode library needed to generate "
                          "QR codes. Please install and try again.")

    return _qrcode.make(uri)
