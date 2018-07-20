
import login
from BioSimSpaceFunction import ObjectStore as objstore

import datetime
import sys

bucket = login.login()

key = sys.argv[1]
filename = sys.argv[2]

objstore.get_object_as_file(bucket, key, filename)
