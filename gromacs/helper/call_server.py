"""
This script helps debugging by creating the login and request
from the .oci/config and hard-coded compartment and bucket names
"""

import oci
import json
import os
import sys

config = oci.config.from_file()
compartment = "ocid1.compartment.oc1..aaaaaaaat33j7w74mdyjenwoinyeawztxe7ri6qkfbm5oihqb5zteamvbpzq"
bucket = "test-gromacs-bucket"

key_lines = open(os.path.expanduser(config["key_file"]), "r").readlines()

del config["key_file"]
config["key_lines"] = key_lines

data = {}

data["login"] = config
data["compartment"] = compartment
data["bucket"] = bucket

try:
    data["task"] = sys.argv[1]
except:
    pass

server = "http://130.61.60.88:8080/r/gromacs/gromacs"

print("Running call to '%s'" % server)
os.system("curl -d '%s' %s" % (json.dumps(data),server))

