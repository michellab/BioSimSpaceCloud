
import asyncio
import fdk
import json

from Acquire.Service import unpack_arguments, get_service_private_key
from Acquire.Service import create_return_value, pack_return_value, \
                            start_profile, end_profile

from Acquire.ObjectStore import string_to_bytes

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

        #encrypted = string_to_bytes("eMWVILuh1HzwTskWmA3acSi/ZKjmo+iwUiBo0eLC71BdfK4zo4zkRorRFD3Fj2Tw86TbcevF1VLHVTXQK73lDtJsUJSTnYQjSHCb8eIk/AaBWlQkzwQhmKeO+f5WCcYSmCOyad/CftZ2QwZxgDBuXF2z7Aa0VlWwYMknp/OoUPMojgHZb3kVkaay+gVvGfeIWHtFfpPHy7ckN3Kijm74GMl8IBLpSLGoSp8PJRakwKPutIgVJR3RRCEvn19Hl6bmoHHnVTyTbGkPcig7Y2XiMSr6ohfiHGJw10PVNEgk2u3oSq9CuMawWSRiCDhuIttzbz/fSwJ70JS5DONqpdG+Gg==")
        encrypted = string_to_bytes(data["data"])

        decrypted = privkey.decrypt(encrypted)

        result["original"] = data["data"]
        result["encrypted"] = ", ".join( [str(x) for x in list(encrypted)] )
        result["message"] = "testing"
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
