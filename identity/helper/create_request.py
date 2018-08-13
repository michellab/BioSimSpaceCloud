"""
This script helps debugging by creating the login and request
from the .oci/config and hard-coded compartment and bucket names
"""

import json

import sys

data = {}

data["username"] = sys.argv[1]
data["password"] = sys.argv[2]

print(json.dumps(data))

