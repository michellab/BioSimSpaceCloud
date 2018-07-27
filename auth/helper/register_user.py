
import json
import os

import sys

data = {}
data["username"] = sys.argv[1]
data["password"] = sys.argv[2]

try:
    data["old_password"] = sys.argv[3]
except:
    pass

server = "http://130.61.60.88:8080/r/auth/register"

print(json.dumps(data))

print("Running call to '%s'" % server)
os.system("curl -d '%s' %s" % (json.dumps(data),server))
