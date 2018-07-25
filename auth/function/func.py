
import json
import fdk
import oci

import os

def handler(ctx, data=None, loop=None):
    """This function will read in json data that identifies the 
       user and supplied password. The user's pem key will be
       retrieved from the object store, password checked, and,
       if passed, then this will be returned as a response"""

    key = None

    pemfile = os.getenv("MASTER_KEY")

    return "pemfile = %s" % pemfile

    if data and len(data) > 0:
        try:
            data = json.loads(data)

            username = data["username"]
            password = data["password"]

            status = -1
            message = "Either this user does not exist or the password is incorrect"

        except Exception as e:
            status = -2
            message = str(e)
    else:
        status = -1
        message = "No username so no data to check"

    response = {}
    response["status"] = status
    response["message"] = message
    response["key"] = key

    return json.dumps(response)

if __name__ == "__main__":
    from fdk import handle
    handle(handler)
