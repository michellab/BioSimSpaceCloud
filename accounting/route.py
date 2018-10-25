
from Acquire.Service import unpack_arguments, get_service_private_key
from Acquire.Service import create_return_value, pack_return_value, \
                            start_profile, end_profile


def handler(ctx, data=None, loop=None):
    """This function routes calls to sub-functions, thereby allowing
       a single accounting function to stay hot for longer"""

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
        elif function == "create_account":
            from create_account import run as _create_account
            result = _create_account(args)
        elif function == "deposit":
            from deposit import run as _deposit
            result = _deposit(args)
        elif function == "get_account_uids":
            from get_account_uids import run as _get_account_uids
            result = _get_account_uids(args)
        elif function == "get_info":
            from get_info import run as _get_info
            result = _get_info(args)
        elif function == "perform":
            from perform import run as _perform
            result = _perform(args)
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
    try:
        from fdk import handle
        handle(handler)
    except Exception as e:
        print("Error running function: %s" % str(e))
        raise
