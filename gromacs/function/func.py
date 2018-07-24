
#### Below needed to add the 'lib' directory in the
#### current directory to the PYTHONPATH
####
import os as _os
import sys as _sys
_sys.path.append(_os.path.join(_os.path.dirname(__file__), "lib"))
####
####

#### All functionality called from BioSimSpaceCloud
from BioSimSpaceCloud import GromacsRunner as gromacs_runner
from BioSimSpaceCloud import ObjectStore as objstore
from BioSimSpaceCloud import Account as account

#### Actual function that is called by Fn
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
            from json import loads
            data = loads(data)
            bucket = account.connect_to_bucket( data["login"],
                                                data["compartment"], 
                                                data["bucket"] )

            # Must clear anything that already exists
            objstore.clear_all_except( bucket, ["input.tar.bz2"] )

            (status, message) = gromacs_runner.run(bucket)
            message = "<output>%s</output>" % message

        except Exception as e:
            status = -2
            message = "<error>%s</error>" % str(e)
    else:
        status = -1
        message = "<error>No input data, so no simulation to run!</error>"

    return {"status" : status, "message" : message }

if __name__ == "__main__":
    from fdk import handle
    handle(handler)
