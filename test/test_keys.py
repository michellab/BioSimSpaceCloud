
import random
import os

from Acquire.Crypto import PublicKey, PrivateKey

class AssertationError(Exception):
    pass

privkey = PrivateKey()
pubkey = privkey.public_key()

message = "Hello World"

sig = privkey.sign(message.encode("utf-8"))
pubkey.verify(sig, message.encode("utf-8"))

c = pubkey.encrypt(message.encode("utf-8"))

m = privkey.decrypt(c).decode("utf-8")
if message != m:
    raise AssertationError()

privkey2 = PrivateKey()
sig2 = privkey2.sign(message.encode("utf-8"))

try:
    pubkey.verify(sig2, message.encode("utf-8"))
    raise AssertationError()
except:
    pass

bytes = privkey.bytes("testPass32")

privkey3 = PrivateKey.read_bytes(bytes, "testPass32")

privkey.write("test.pem", "testPass32")

privkey3 = PrivateKey.read("test.pem", "testPass32")

bytes = pubkey.bytes()
pubkey2 = PublicKey.read_bytes(bytes)

long_message = str([random.getrandbits(8) for _ in range(4096)]).encode("utf-8")

c = pubkey.encrypt(long_message)

m = privkey.decrypt(c)

if m != long_message:
    print(long_message[0:32], m[0:32])
    raise AssertationError()

os.unlink("test.pem")
