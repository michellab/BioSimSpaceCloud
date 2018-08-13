
import json as _json

try:
    import pycurl as _pycurl
    has_pycurl = True
except:
    has_pycurl = False

from urllib.parse import urlencode as _urlencode
from io import BytesIO as _BytesIO

__all__ = [ "call_function" ]

class RemoteFunctionCallError(Exception):
    pass

def call_function(function_url, arg_dict):
    """Call the remote function at 'function_url' passing
       in named function arguments in 'arg_dict'"""

    if not has_pycurl:
        raise RemoteFunctionCallError("Cannot call remote functions as "
                   "the pycurl module cannot be imported! It needs "
                   "to be installed into this python session...")

    arg_json = _json.dumps(arg_dict)

    buffer = _BytesIO()
    c = _pycurl.Curl()
    c.setopt(c.URL, function_url)
    c.setopt(c.WRITEDATA, buffer)
    c.setopt(c.POSTFIELDS, arg_json)
    c.perform()
    c.close()

    # All of the output from Acquire will be utf-8 encoded
    result_json = buffer.getvalue().decode("utf-8")

    # may need to multi-decode the json...
    while isinstance(result_json,str):
        try:
            result_json = _json.loads(result_json)
        except:
            raise RemoteFunctionCallError("Error calling '%s'. Could not json decode "
                     "the returned string: '%s'" % (function_url,result_json))
            
    if isinstance(result_json,dict):
        if len(result_json) == 1 and "error" in result_json:
            raise RemoteFunctionCallError("Error calling '%s'. Server returned the "
                     "error string: '%s'" % (function_url,result_json["error"]))

    return result_json
