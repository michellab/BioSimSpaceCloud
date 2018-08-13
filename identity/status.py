
import json
import fdk
import oci

import os

from BioSimSpaceCloud import ObjectStore
from identityaccount import loginToIdentityAccount

def handler(ctx, data=None, loop=None):
    """This function will read in json data that identifies the 
       user and supplied password. The user's pem key will be
       retrieved from the object store, password checked, and,
       if passed, then this will be returned as a response"""

    # The first step is to log into the primary identity account.
    identity_client = loginToIdentityAccount()

    response = { "log" : ObjectStore.get_log(identity_client) }

    return json.dumps(response)

if __name__ == "__main__":
    from fdk import handle
    handle(handler)
