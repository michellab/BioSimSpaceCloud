
from Acquire import User

import sys

user = User(sys.argv[1])
request = user.requestLogin()

print(request)
