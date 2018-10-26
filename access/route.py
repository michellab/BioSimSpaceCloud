
import asyncio
import fdk

from Acquire.Service import unpack_arguments, get_service_private_key
from Acquire.Service import create_return_value, pack_return_value, \
                            start_profile, end_profile


async def handler(ctx, data=None, loop=None):
    """This function routes calls to sub-functions, thereby allowing
       a single access function to stay hot for longer"""

    pr = start_profile()

    args = unpack_arguments(data, get_service_private_key)

    try:
        function = str(args["function"])
    except:
        function = None

    try:
        if function is None:
            from root import run as _root
            result = _root(args)
        elif function == "request":
            from request import run as _request
            result = _request(args)
        elif function == "request_bucket":
            from request_bucket import run as _request_bucket
            result = _request_bucket(args)
        elif function == "setup":
            from setup import run as _setup
            result = _setup(args)
        else:
            result = {"status": -1,
                      "message": "Unknown function '%s'" % function}

    except Exception as e:
        result = {"status": -1,
                  "message": "Error %s: %s" % (e.__class__, str(e))}

    end_profile(pr, result)

    return pack_return_value(result, args)


if __name__ == "__main__":
    fdk.handle(handler)
