
import json
import fdk
import oci

import os

from Acquire import ObjectStore
from identityaccount import loginToIdentityAccount

def handler(ctx, data=None, loop=None):
    """This function will read in json data that identifies the 
       user and supplied password. The user's pem key will be
       retrieved from the object store, password checked, and,
       if passed, then this will be returned as a response"""

    try:
        # The first step is to log into the primary identity account.
        identity_client = loginToIdentityAccount()

        response = { "message" : "The identity service account works :-)",
                     "status" : 0 }

        return json.dumps(response).encode("utf-8")

    except Exception as e:
        response = { "error" : str(e) }
        return json.dumps(response).encode("utf-8")

if __name__ == "__main__":
    from fdk import handle
    handle(handler)
