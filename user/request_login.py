
from Acquire import User

import sys

server = "http://130.61.60.88:8080"
service = "r/auth/request-login"

user = User.requestLogin("%s/%s" % (server, service), sys.argv[1])
 
print(user)

