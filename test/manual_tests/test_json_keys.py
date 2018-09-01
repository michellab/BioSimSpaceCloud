

from Acquire.Crypto import PrivateKey
from Acquire.Service import pack_arguments, unpack_arguments

import random

privkey = PrivateKey()
pubkey = privkey.public_key()

args = { "message" : "Hello, this is a message",
         "status" : 0,
         "long" : [random.random() for _ in range(1000)] }

#print(args)

packed = pack_arguments(args)

#print(packed)

crypted = pubkey.encrypt(packed)

#print(crypted)

uncrypted = privkey.decrypt(crypted)

#print(uncrypted)

unpacked = unpack_arguments(uncrypted)

#print(unpacked)

assert( args == unpacked )
