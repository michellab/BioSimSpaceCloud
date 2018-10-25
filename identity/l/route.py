
from Acquire.Service import unpack_arguments, get_service_private_key

import fdk

from fdk import response


def handler(ctx, data=None, loop=None):
    """This function routes to various dynamic html pages that
       are needed by the identity service
    """

    args = unpack_arguments(data, get_service_private_key)

    try:
        function = str(args["function"])
    except:
        function = None

    try:
        if function is None:
            from root import run as _root
            result = _root(args)
        else:
            result = {"status": -1,
                      "message": "Unknown function '%s'" % function}

    except Exception as e:
        result = {"status": -1,
                  "message": "Error %s: %s" % (e.__class__, str(e))}

    return response.RawResponse(
        ctx,
        status_code=200,
        headers={},
        response_data=str(result)
    )


if __name__ == "__main__":
    try:
        from fdk import handle
        handle(handler)
    except Exception as e:
        print("Error running function: %s" % str(e))
        raise
