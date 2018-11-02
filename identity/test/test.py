
import asyncio
import fdk
import json

from Acquire.Service import unpack_arguments, get_service_private_key
from Acquire.Service import create_return_value, pack_return_value, \
                            start_profile, end_profile

from Acquire.Crypto import PrivateKey, PublicKey

async def handler(ctx, data=None, loop=None):
    """This function just reflects back the json that is supplied.
       This is useful for debugging clients that are calling this
       server
    """

    result = {}

    try:
        data = json.loads(data)

        privkey = get_service_private_key()

        encrypted = data["data"]
        plain = privkey.decrypt(encrypted)

        result["message"] = plain

    except Exception as e:
        message = {"status": -1,
                   "message": "Error packing results: %s" % e}
        return json.dumps(message)
    except:
        message = {"status": -1,
                   "message": "Error packing results: Unknown error"}
        return json.dumps(message)

    return json.dumps(result)

if __name__ == "__main__":
    try:
        fdk.handle(handler)
    except Exception as e:
        print({"message": "Error! %s" % str(e), "status": -1})
    except:
        print({"message": "Unknown error!", "status": -1})
