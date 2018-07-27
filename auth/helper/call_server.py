"""
This script helps debugging by creating the login and request
from the .oci/config and hard-coded compartment and bucket names
"""

import oci
import json
import os

import sys

data = {}

try:
    service = sys.argv[1]
except:
    service = ""

server = "http://130.61.60.88:8080/r/auth/%s" % service

if service == "login" or service == "register":
    data["username"] = sys.argv[2]
    data["password"] = sys.argv[3]

print("Running call to '%s'" % server)
os.system("curl -d '%s' %s" % (json.dumps(data),server))
