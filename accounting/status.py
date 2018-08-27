
import json
import os

from Acquire.Service import unpack_arguments, create_return_value, pack_return_value
from Acquire.Service import get_service_info, get_service_private_key

def handler(ctx, data=None, loop=None):
    """This function return the status and service info"""

    status = 0
    message = None
    service = None
    error = None

    log = []

    args = unpack_arguments(data, get_service_private_key)

    try:
        service = get_service_info()

        status = 0
        message = "Success"

    except Exception as e:
        error = e

    return_value = create_return_value(status, message, log, error)

    if service:
        return_value["service_info"] = service.to_data()

    return pack_return_value(return_value, args)

if __name__ == "__main__":
    try:
        from fdk import handle
        handle(handler)
    except Exception as e:
        print("Error running function: %s" % str(e))
        raise
