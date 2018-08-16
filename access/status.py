
import json
import fdk
import oci

import os

from Acquire import ObjectStore
from accessaccount import loginToAccessAccount

def handler(ctx, data=None, loop=None):
    """This function gets the status of the access service"""

    try:
        # The first step is to log into the primary access account.
        access_client = loginToAccessAccount()

       	response = { "message" : "The access service account works :-)",
       	       	     "status" :	0 }

        return json.dumps(response).encode("utf-8")

    except Exception as e:
        response = { "error" : str(e) }
        return json.dumps(response).encode("utf-8")

if __name__ == "__main__":
    from fdk import handle
    handle(handler)
