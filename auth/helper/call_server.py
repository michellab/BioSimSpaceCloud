"""
This script helps debugging by creating the login and request
from the .oci/config and hard-coded compartment and bucket names
"""

import oci
import json
import os

import sys

data = {}
data["username"] = sys.argv[1]
data["password"] = sys.argv[2]

server = "http://130.61.60.88:8080/r/auth/auth"

print("Running call to '%s'" % server)
os.system("curl -d '%s' %s" % (json.dumps(data),server))

