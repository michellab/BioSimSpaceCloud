
import json as _json

try:
    import pycurl as _pycurl
    has_pycurl = True
except:
    has_pycurl = False

from urllib.parse import urlencode as _urlencode
from io import BytesIO as _BytesIO

import base64 as _base64

__all__ = [ "call_function", "bytes_to_string", "string_to_bytes", 
            "string_to_encoded", "encoded_to_string",
            "encrypt_response", "decrypt_arguments" ]

def string_to_encoded(s):
    """Return the passed unicode string encoded to a safely
       encoded base64 utf-8 string"""
    return bytes_to_string(s.encode("utf-8"))

def encoded_to_string(b):
    """Return the passed encoded base64 utf-8 string converted
       back into a unicode string"""
    return string_to_bytes(b).decode("utf-8")

def bytes_to_string(b):
    """Return the passed binary bytes safely encoded to
       a base64 utf-8 string"""
    if b is None:
        return None
    else:
        return _base64.b64encode(b).decode("utf-8")

def string_to_bytes(s):
    """Return the passed base64 utf-8 encoded binary data
       back converted from a string back to bytes. Note that
       this can only convert strings that were encoded using
       bytes_to_string - you cannot use this to convert 
       arbitrary strings to bytes"""
    if s is None:
        return None
    else:
        return _base64.b64decode(s.encode("utf-8"))

class RemoteFunctionCallError(Exception):
    pass

def encrypt_response(result, key):
    """Call this to encrypt the response to a function call using
       the passed key""

    if isinstance(key, dict):
        # extract the key from the data dictionary
        key = _PublicKey.read_bytes( _string_to_bytes(key["encrypt_response_key"]) )

    result = _json.dumps(result).encode("utf-8")

    response = {}
    response["encrypted_response"] = _bytes_to_string(key.encrypt(result))

    return response

def decrypt_arguments(args, key):
   """Call this to decrypt the passed arguments using the passed key"""

   if "encrypted" in args and args["encrypted"]:
       return key.decrypt( args["data"] ).decode("utf-8")
   else:
       return args

def call_function(function_url, arg_dict, arg_key=None, response_key=None):
    """Call the remote function at 'function_url' passing
       in named function arguments in 'arg_dict'. If 'arg_key' is supplied,
       the encrypt the arguments using 'arg_dict'. If 'response_key'
       is supplied, then tell the remote server to encrypt the response
       using the public version of 'response_key', so that we can
       decrypt it in the response"""

    if not has_pycurl:
        raise RemoteFunctionCallError("Cannot call remote functions as "
                   "the pycurl module cannot be imported! It needs "
                   "to be installed into this python session...")

    if response_key:
        arg_dict["encrypt_response_key"] = _bytes_to_string(
                                              response_key.public_key().bytes() )

    arg_json = _json.dumps(arg_dict)

    if arg_key:
        encrypted_args = arg_key.encrypt( arg_json.encode("utf-8") )
        arg_json = { "encrypted" : True,
                     "data" : encrypted_args }

        arg_json = _json.dumps(arg_json)

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

    # is the response actually encrypted?
    if response_key:
        try:
            encrypted_response = _string_to_bytes(result_json["encrypted_response"])
        except:
            encrypted_response = None

        if encrypted_response
            result_json = response_key.decrypt(encrypted_response).decode("utf-8")

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
        elif "status" in result_json:
            if result_json["status"] != 0:
                raise RemoteFunctionCallError("Error calling '%s'. Server returned "
                     "error code '%d' with message '%s'" % \
                        (function_url,result_json["status"],result_json["message"]))

    return result_json

