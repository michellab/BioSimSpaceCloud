
import sys

from Acquire import call_function

args = {}

service = sys.argv[1]
args["service_url"] = service

args["password"] = sys.argv[2]
args["otpcode"] = sys.argv[3]

try:
    args["new_service"] = sys.argv[4]
except:
    pass

response = call_function("%s/setup" % service, args)

print(response)
