
import login
from BioSimSpaceCloud import ObjectStore as objstore

import datetime

bucket = login.login()

objs = objstore.get_all_strings(bucket, "log")

timestamps = list(objs.keys())
timestamps.sort()

for timestamp in timestamps:
    d = datetime.datetime.fromtimestamp(float(timestamp))
    m = objs[timestamp]
    print("%s: %s" % (d,m))
