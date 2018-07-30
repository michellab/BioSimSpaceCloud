
import json as _json

import pycurl as _pycurl
from urllib.parse import urlencode as _urlencode
from io import BytesIO as _BytesIO

__all__ = [ "call_function" ]

def call_function(function_url, arg_dict):
    """Call the remote function at 'function_url' passing
       in named function arguments in 'arg_dict'"""

    arg_json = _json.dumps(arg_dict)

    buffer = _BytesIO()
    c = _pycurl.Curl()
    c.setopt(c.URL, function_url)
    c.setopt(c.WRITEDATA, buffer)
    c.setopt(c.POSTFIELDS, arg_json)
    c.perform()
    c.close()

    result_json = buffer.getvalue().decode("utf-8")

    return _json.loads(result_json)
