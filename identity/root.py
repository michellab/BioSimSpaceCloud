
import json
import os

from Acquire.Service import unpack_arguments, get_service_private_key, \
                            create_return_value
from Acquire.Service import get_service_info, pack_return_value, \
                            start_profile, end_profile


def handler(ctx, data=None, loop=None):
    """This function return the status and service info"""

    pr = start_profile()

    status = 0
    message = None
    service = None

    log = []

    args = unpack_arguments(data, get_service_private_key)

    try:
        service = get_service_info()

        status = 0
        message = "Success"

    except Exception as e:
        status = -1
        message = "Error %s: %s" % (e.__class__, str(e))

    return_value = create_return_value(status, message, log)

    if service:
        return_value["service_info"] = service.to_data()

    end_profile(pr, return_value)

    # Pass the original arguments when creating the return value
    # as it may specify different formats for return, or provide
    # an encryption key to use for encrypting the result
    return pack_return_value(return_value, args)

if __name__ == "__main__":
    from fdk import handle
    handle(handler)
