import fdk
import oci
import json
import os
import sys

import gromacs_runner

def log(message):
    sys.stderr.write( str(message) )
    sys.stderr.write("\n")

def get_login(login):
    """This function turns the passed login details into
       a valid oci login, and actually logs in :-) """

    # first, we need to convert the 'login' so that it puts
    # the private key into a file
    keyfile = "/tmp/key.pem"

    try:
        FILE = open(keyfile, "w")

        for line in login["key_lines"]:
            FILE.write(line)
            
        FILE.close()                    
        os.chmod(keyfile, 0o0600)

        del login["key_lines"]
        login["key_file"] = keyfile

        # validate the config is ok
        oci.config.validate_config(login)

    except:
        os.remove(keyfile)
        raise

    return login

def connect_to_bucket( login_details, compartment, bucket_name ):
    """Connect to the object store compartment 'compartment'
       using the passed 'login_details', returning a handle to the 
       bucket associated with 'bucket'"""

    login = get_login(login_details)
    bucket = {}

    try:
        client = oci.object_storage.ObjectStorageClient(login)
        bucket["client"] = client
        bucket["compartment_id"] = compartment

        namespace = client.get_namespace().data
        bucket["namespace"] = namespace

        bucket["bucket"] = client.get_bucket(namespace, bucket_name).data
        bucket["bucket_name"] = bucket_name
    except:
        os.remove( os.path.abspath(login["key_file"]) )
        raise

    os.remove( os.path.abspath(login["key_file"]) )

    return bucket

def handler(ctx, data=None, loop=None):
    """This function will read in json data that will provide
       authentication info to log into a object store, together
       with a key in the store in which to find the input data
       for the gromacs simulation. This function will use that
       key to download the data onto this node, run the gromacs
       simulation, and then output to a sub-key of the 
       input key in the object store. This function is designed
       to be called asynchronously by Fn, as it will only
       return when the gromacs simulation is complete."""

    if data and len(data) > 0:
        try:
            data = json.loads(data)
            bucket = connect_to_bucket( data["login"],
                                        data["compartment"], 
                                        data["bucket"] )

            (status, message) = gromacs_runner.run(bucket)

        except Exception as e:
            status = -2
            log(str(e))
            message = "Error:\n%s" % str(e)
    else:
        status = -1
        message = "No input data, so no simulation to run!"

    return {"status" : status, "message" : message }

if __name__ == "__main__":
    fdk.handle(handler)
