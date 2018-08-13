
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

    # Need to double-un-json it, as the first json returns
    # a Python string, and then we need to json decode
    # this string into a dictionary

    try:
        return _json.loads(_json.loads(result_json))
    except Exception as e:
        raise RemoteFunctionCallError("Could not interpret the "
               "returned json data '%s' : %s" % (result_json,str(e)) )
