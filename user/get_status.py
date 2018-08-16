
from Acquire import call_function

# Get the status output of all of the services
server = "http://130.61.60.88:8080/r"

# First, the identity service
print( call_function("%s/identity" % server, {}) )

# Next, the access service
print( call_function("%s/access" % server, {}) )

# Finally, the accounting service
print( call_function("%s/accounting" % server, {}) )
