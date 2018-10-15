
import json

from Acquire.Service import unpack_arguments, create_return_value, \
                            pack_return_value
from Acquire.Service import login_to_service_account, Service, \
                            get_service_private_key
from Acquire.Service import call_function

from Acquire.Crypto import PrivateKey

from Acquire.ObjectStore import ObjectStore, string_to_bytes

from Acquire.Access import Request


class RequestError(Exception):
    pass


def handler(ctx, data=None, loop=None):
    """This function is used to handle requests to access resources"""

    status = 0
    message = None
    log = []

    access_token = None

    args = unpack_arguments(data, get_service_private_key)

    try:
        request = Request.from_data(args["request"])
        access_token = request.to_data()

    except Exception as e:
        status = -1
        message = "Error %s: %s" % (e.__class__, str(e))

    return_value = create_return_value(status, message, log)

    if access_token:
        return_value["access_token"] = access_token

    return pack_return_value(return_value, args)

if __name__ == "__main__":
    try:
        from fdk import handle
        handle(handler)
    except Exception as e:
        print("Error running function: %s" % str(e))
        raise
