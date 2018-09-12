"""
Acquire : (C) Christopher Woods 2018

This module contains the interfaces to the object store that provides the
storage of all state for the system. As such, this is the foundation
module that is unlikely to be used by the user, but instead is used
by most of the other modules.
"""

from ._objstore import *
from ._encoding import *
from ._mutex import *
from ._oci_objstore import *
from ._testing_objstore import *
from ._errors import *
