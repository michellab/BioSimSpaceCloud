
import json
import os

import sys

data = {}
data["username"] = sys.argv[1]

public_key = sys.argv[2]
public_cert = sys.argv[3]

data["public_key"] = open(public_key,"r").readlines()
data["public_certificate"] = open(public_cert,"r").readlines()
data["ipaddr"] = "somewhere!"

server = "http://130.61.60.88:8080/r/identity/request-login"

print("Running call to '%s'" % server)
os.system("curl -d '%s' %s" % (json.dumps(data),server))
