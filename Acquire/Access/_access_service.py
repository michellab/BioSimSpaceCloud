
import uuid as _uuid
from copy import copy as _copy

from ._keys import PrivateKey as _PrivateKey
from ._keys import PublicKey as _PublicKey

from ._function import call_function as _call_function

from ._service import Service as _Service

__all__ = [ "AccessService" ]

class ServiceError(Exception):
    pass

class AccessService(_Service):
    """This is a specialisation of Service for Access Services"""
    def __init__(self, other=None):
        if isinstance(other,_Service):
            self.__dict__ = _copy(other.__dict__)

            if not self.is_access_service():
                raise ServiceError("Cannot construct an IdentityService from "
                        "a service which is not an access service!")
        else:
            _Service.__init__(self)

