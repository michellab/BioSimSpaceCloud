
import login
from BioSimSpaceCloud import ObjectStore as objstore

import datetime
import sys

bucket = login.login()

for key in sys.argv[1:]:
    s = objstore.get_string_object(bucket, key)
    print("%s : %s" % (key,s))
