
import asyncio
import fdk

from Acquire.Service import unpack_arguments, get_service_private_key
from Acquire.Service import create_return_value, pack_return_value, \
                            start_profile, end_profile


async def handler(ctx, data=None, loop=None):
    """This function routes calls to sub-functions, thereby allowing
       a single identity function to stay hot for longer"""

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
        elif function == "request_login":
            from request_login import run as _request_login
            result = _request_login(args)
        elif function == "get_keys":
            from get_keys import run as _get_keys
            result = _get_keys(args)
        elif function == "get_status":
            from get_status import run as _get_status
            result = _get_status(args)
        elif function == "login":
            from login import run as _login
            result = _login(args)
        elif function == "logout":
            from logout import run as _logout
            result = _logout(args)
        elif function == "register":
            from register import run as _register
            result = _register(args)
        elif function == "request_login":
            from request_login import run as _request_login
            result = _request_login(args)
        elif function == "setup":
            from setup import run as _setup
            result = _setup(args)
        elif function == "whois":
            from whois import run as _whois
            result = _whois(args)
        elif function == "test":
            from test import run as _test
            result = _test(args)
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
