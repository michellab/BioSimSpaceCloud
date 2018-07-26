"""
This script writes the login information (pem key etc.) that is needed
by the identity service to log onto the object store as the
identity admin user account
"""

import json
import sys
import os

"""
[DEFAULT]
user=ocid1.user.oc1..aaaaaaaahxlrqhcgfzdv52ias5yt6go6ybgmb5hv7at5amepal22tagvaczq
fingerprint=11:7e:8f:d4:2a:c8:73:e9:0c:e6:08:94:16:3b:72:e4
key_file=~/.oci/oci_api_key.pem
pass_phrase=XXXXXX
tenancy=ocid1.tenancy.oc1..aaaaaaaa3eiex6fbfj626uwhs3dg24oygknrhhgfj4khqearluf4i74zdt2a
region=eu-frankfurt-1
"""

data = {}

# OCID for the user "bss-auth-service"
data["user"] = "ocid1.user.oc1..aaaaaaaarifc7gs7inqujkuklltlqilikqh2i24y43erqoe5kdlcbbtalmra"

# Fingerprint for the login keyfile
data["fingerprint"] = "45:1d:e1:33:10:ae:d5:47:57:9d:aa:44:46:82:55:5b"

# The keyfile itself - we will now read the file and pull it into text
keyfile = sys.argv[1]
data["key_lines"] = open(sys.argv[1],"r").readlines()

# The tenancy in which this user and everything exists!
data["tenancy"] = "ocid1.tenancy.oc1..aaaaaaaa3eiex6fbfj626uwhs3dg24oygknrhhgfj4khqearluf4i74zdt2a"

# The region for this tenancy
data["region"] = "eu-frankfurt-1"

print(json.dumps(data))

os.system("fn config app auth LOGIN_JSON '%s'" % json.dumps(data))
