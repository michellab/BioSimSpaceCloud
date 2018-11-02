
import asyncio
import fdk
import json

from Acquire.Service import unpack_arguments, get_service_private_key
from Acquire.Service import create_return_value, pack_return_value, \
                            start_profile, end_profile

from Acquire.ObjectStore import string_to_bytes

from Acquire.Crypto import PrivateKey, PublicKey

from cryptography import fernet

async def handler(ctx, data=None, loop=None):
    """This function just reflects back the json that is supplied.
       This is useful for debugging clients that are calling this
       server
    """

    result = {}

    try:
        data = json.loads(data)

        privkey = get_service_private_key()

        encrypted = string_to_bytes(data["data"])

        decrypted = privkey.decrypt(encrypted[0:256])

        symkey = decrypted
        message = data["fernet"]

        try:
            f = fernet.Fernet(symkey)
        except:
            f = fernet.Fernet(symkey.decode("utf-8"))

        try:
            message = f.decrypt(message)
        except:
            message = f.decrypt(message.encode("utf-8"))

        #result["encrypted"] = ", ".join( [str(x) for x in list(encrypted)] )
        result["message"] = str(message)
        result["decrypted"] = str(decrypted)
        result["status"] = -1

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
    fdk.handle(handler)
