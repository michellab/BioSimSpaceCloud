
import sys

from Acquire import call_function, User

args = { "short_uid" : sys.argv[1],
         "username" : sys.argv[2],
         "password" : sys.argv[3],
         "otpcode" : sys.argv[4] }

user = User(sys.argv[2])

login_url = "%s/login" % user.identity_service_url()

result = call_function(login_url, args)

print(result)

