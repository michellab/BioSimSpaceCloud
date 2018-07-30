
from Acquire import PublicKey, PrivateKey

class AssertationError(Exception):
    pass

privkey = PrivateKey()
pubkey = privkey.public_key()

message = "Hello World"

sig = privkey.sign(message.encode("utf-8"))
pubkey.verify(sig, message.encode("utf-8"))

privkey2 = PrivateKey()
sig2 = privkey2.sign(message.encode("utf-8"))

try:
    pubkey.verify(sig2, message.encode("utf-8"))
    raise AssertationError()
except:
    pass
 
