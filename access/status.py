
import json
import fdk
import os

from Acquire import ObjectStore, Service
from accessaccount import loginToAccessAccount

def handler(ctx, data=None, loop=None):
    """This function return the status and service info"""

    if not (data and len(data) > 0):
        return    

    status = 0
    message = None
    service = None

    log = []

    try:
        # data is already a decoded unicode string
        data = json.loads(data)

        bucket = loginToAccessAccount()

        service_key = "_service_info"

        service = ObjectStore.get_object_from_json(bucket, service_key)

        if service:
            service = Service.from_data(service)

        status = 0
        message = "Success"

    except Exception as e:
        status = -1
        message = "Error %s: %s" % (e.__class__,str(e))

    response = {}
    response["status"] = status
    response["message"] = message
    
    if service:
        response["service_info"] = service.to_data()

    if log:
        response["log"] = log

    return json.dumps(response).encode("utf-8")

if __name__ == "__main__":
    from fdk import handle
    handle(handler)
