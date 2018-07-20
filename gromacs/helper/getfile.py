"""
This script helps debugging by creating the login and request
from the .oci/config and hard-coded compartment and bucket names
"""

import oci
import json
import os
import sys



key = sys.argv[1]
filename = sys.argv[2]

## Now load up the key and get the bucket/compartment ID
config = oci.config.from_file()
compartment = "ocid1.compartment.oc1..aaaaaaaat33j7w74mdyjenwoinyeawztxe7ri6qkfbm5oihqb5zteamvbpzq"
bucket = "test-gromacs-bucket"

key_lines = open(os.path.expanduser(config["key_file"]), "r").readlines()

del config["key_file"]
config["key_lines"] = key_lines
## Config is now in the format used by the system as a key/bucket


