
from Acquire import User

import sys

user = User(sys.argv[1])

try:
    request = user.request_login()
    print(request)
except Exception as e:
    print(e)

logged_in = user.wait_for_login(timeout=10)

if not logged_in:
    print("Still not logged in after 10 seconds? Waiting forever!")
    user.wait_for_login()


