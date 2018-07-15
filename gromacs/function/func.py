import fdk
import oci
import json

import gromacs_runner

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
            (status, message) = gromacs_runner.run( json.loads(data) )

        except Exception as e:
            status = -2
            message = "Failed to run simulation:\n%s" % str(e)
    else:
        status = -1
        message = "No input data, so no simulation to run!"

    return {"status" : status, "message" : message }

if __name__ == "__main__":
    fdk.handle(handler)
