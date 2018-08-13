
from Acquire import User

import sys

user = User(sys.argv[1])

try:
    request = user.requestLogin()
    print(request)
except Exception as e:
    print(e)

user.waitForLogin()
