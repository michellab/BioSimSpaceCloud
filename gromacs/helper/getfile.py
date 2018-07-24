
import login
from BioSimSpaceCloud import ObjectStore as objstore

import datetime
import sys

bucket = login.login()

key = sys.argv[1]

try:
    filename = sys.argv[2]
except:
    filename = None

if filename:
    objstore.get_object_as_file(bucket, key, filename)
else:
    data = objstore.get_string_object(bucket, key)
    print(data)

