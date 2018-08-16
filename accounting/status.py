
import json
import fdk
import oci

import os

from Acquire import ObjectStore
from accountingaccount import loginToAccountingAccount

def handler(ctx, data=None, loop=None):
    """This function gets the status of the accounting service"""

    try:
        # The first step is to log into the primary accounting account.
        accounting_client = loginToAccountingAccount()

        return json.dumps( {"status" : str(0)} ).encode("utf-8")

    except Exception as e:
        response = { "error" : str(e) }
        return json.dumps(response).encode("utf-8")

if __name__ == "__main__":
    from fdk import handle
    handle(handler)
