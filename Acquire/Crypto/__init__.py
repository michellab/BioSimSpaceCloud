""" 
Acquire.Crypto  (C) Christopher Woods 2018

This module contains thin wrappers around industry standard cryptography
libraries. The aim is to provide a simple interface that ensures that
all cryptography in Acquire uses best practice
"""

from ._keys import *
from ._otp import *
from ._errors import *
