
from Acquire import User

import sys

user = User(sys.argv[1])

try:
    request = user.requestLogin()
    print(request)
except Exception as e:
    print(e)

logged_in = user.waitForLogin(timeout=10)

if not logged_in:
    print("Still not logged in after 10 seconds? Waiting forever!")
    user.waitForLogin()


