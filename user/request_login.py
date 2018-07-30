
from Acquire import User

import sys

server = "http://130.61.60.88:8080"
service = "r/auth/request-login"

user = User(sys.argv[1])
request = user.requestLogin("%s/%s" % (server, service))
 
print(request)
