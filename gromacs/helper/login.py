
import oci
import json
import os
import sys

from BioSimSpaceFunction import Account as account

def login():
    config = oci.config.from_file()
    compartment = "ocid1.compartment.oc1..aaaaaaaat33j7w74mdyjenwoinyeawztxe7ri6qkfbm5oihqb5zteamvbpzq" 
    bucket = "test-gromacs-bucket"

    key_lines = open(os.path.expanduser(config["key_file"]), "r").readlines()

    del config["key_file"]
    config["key_lines"] = key_lines

    data = {}

    data["login"] = config
    data["compartment"] = compartment
    data["bucket"] = bucket

    bucket = account.connect_to_bucket( data["login"],
                                        data["compartment"],
                                        data["bucket"] )
    return bucket

