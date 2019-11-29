"""
XTEA Block Encryption Algorithm

Author: Paul Chakravarti (paul_dot_chakravarti_at_gmail_dot_com)
License: Public Domain

This module provides a Python implementation of the XTEA block encryption
algorithm (http://www.cix.co.uk/~klockstone/xtea.pdf).

The module implements the basic XTEA block encryption algortithm
(`xtea_encrypt`/`xtea_decrypt`) and also provides a higher level `crypt`
function which symmetrically encrypts/decrypts a variable length string using
XTEA in OFB mode as a key generator. The `crypt` function does not use
`xtea_decrypt` which is provided for completeness only (but can be used
to support other stream modes - eg CBC/CFB).

This module is intended to provide a simple 'privacy-grade' Python encryption
algorithm with no external dependencies. The implementation is relatively slow
and is best suited to small volumes of data. Note that the XTEA algorithm has
not been subjected to extensive analysis (though is believed to be relatively
secure - see http://en.wikipedia.org/wiki/XTEA). For applications requiring
'real' security please use a known and well tested algorithm/implementation.

The security of the algorithm is entirely based on quality (entropy) and
secrecy of the key. You should generate the key from a known random source and
exchange using a trusted mechanism. In addition, you should always use a random
IV to seed the key generator (the IV is not sensitive and does not need to be
exchanged securely)

    >>> iv = 'ABCDEFGH'
    >>> z = crypt('0123456789012345','Hello There',iv)
    >>> tohex(z)
    'fe196d0a40d6c222b9eff3'
    >>> crypt('0123456789012345',z,iv)
    'Hello There'

For adapya changed: 2017/05/17
- adapted to run in Python3 and Python 2.6 and greater
- in Python3 Unicode chars > \u00ff are not supported
"""

import os
import struct
import sys

#: PY3, urandom3(), fromhex() and tohex() help running in Python2 and Python3
PY3 = True if sys.version_info.major > 2 else False

urandom3 = lambda n: os.urandom(n).decode('Latin1') if PY3 else os.urandom(n)

fromhex = lambda s: bytes.fromhex(s).decode('Latin1') if PY3 else s.decode('hex')

def tohex(s):
    """ return hex string in PY2 and PY3 """
    if PY3:
        if type(s) is type(''): # convert from string to bytes first
            return s.encode('latin1').hex()
        else:
            return s.hex()
    else:
        return s.encode('hex')

def crypt(key,data,iv=b'\00\00\00\00\00\00\00\00',n=32):
    """
        Encrypt/decrypt variable length string using XTEA cypher as
        key generator (OFB mode)
        * key = 128 bit (16 char)
        * iv = 64 bit (8 char)
        * data = string (any length)

        In Python3 the bytes or string types may be used with
        character values not exceding \u00ff (Latin1)

        >>> key = urandom3(16)
        >>> iv = urandom3(8)
        >>> data = urandom3(30)
        >>> z = crypt(key,data,iv)
        >>> crypt(key,z,iv) == data
        True

    """

    if PY3: # convert string to bytes
        if type(data) is type(''): data = data.encode('latin1') # better than ASCII
        if type(key) is type(''): key = key.encode('latin1')
        if type(iv) is type(''): iv = iv.encode('latin1')

    def keygen(key,iv,n):
        while True:
            iv = xtea_encrypt(key,iv,n)
            if PY3:
                for k in iv.encode('Latin1'):
                    yield k
            else:
                for k in iv:
                    yield ord(k)

    if PY3: # iterating on bytestring returns ord of each byte
        xor = [ x^y for (x,y) in zip(data, keygen(key,iv,n))   ]
        return bytes(xor).decode('Latin1')
    else:
        xor = [ chr(x^y) for (x,y) in zip(map(ord,data),keygen(key,iv,n))   ]
        return "".join(xor)

def xtea_encrypt(key,block,n=32,endian="!"):
    """
        Encrypt 64 bit data block using XTEA block cypher
        * key = 128 bit (16 char)
        * block = 64 bit (8 char)
        * n = rounds (default 32)
        * endian = byte order (see 'struct' doc - default big/network)

        >>> z = xtea_encrypt('0123456789012345','ABCDEFGH')
        >>> tohex(z)
        'b67c01662ff6964a'

        Only need to change byte order if sending/receiving from
        alternative endian implementation

        >>> z = xtea_encrypt('0123456789012345','ABCDEFGH',endian="<")
        >>> tohex(z)
        'ea0c3d7c1c22557f'

    """
    if PY3: # convert string to bytes
        if type(block) is type(''): block = block.encode('latin1') # better than ASCII
        if type(key) is type(''): key = key.encode('latin1')


    v0,v1 = struct.unpack(endian+"2L",block)
    k = struct.unpack(endian+"4L",key)
    sum,delta,mask = 0,0x9e3779b9,0xffffffff

    for round in range(n):
        v0 = (v0 + (((v1<<4 ^ v1>>5) + v1) ^ (sum + k[sum & 3]))) & mask
        sum = (sum + delta) & mask
        v1 = (v1 + (((v0<<4 ^ v0>>5) + v0) ^ (sum + k[sum>>11 & 3]))) & mask

    if PY3:
        return struct.pack(endian+"2L",v0,v1).decode('Latin1')
    else:
        return struct.pack(endian+"2L",v0,v1)


def xtea_decrypt(key,block,n=32,endian="!"):
    """
        Decrypt 64 bit data block using XTEA block cypher
        * key = 128 bit (16 char)
        * block = 64 bit (8 char)
        * n = rounds (default 32)
        * endian = byte order (see 'struct' doc - default big/network)

        >>> z = fromhex('b67c01662ff6964a')
        >>> xtea_decrypt('0123456789012345',z)
        'ABCDEFGH'

        Only need to change byte order if sending/receiving from
        alternative endian implementation

        >>> z = fromhex('ea0c3d7c1c22557f')
        >>> xtea_decrypt('0123456789012345',z,endian="<")
        'ABCDEFGH'

    """
    if PY3: # convert string to bytes
        if type(block) is type(''): block = block.encode('latin1') # better than ASCII
        if type(key) is type(''): key = key.encode('latin1')

    v0,v1 = struct.unpack(endian+"2L",block)
    k = struct.unpack(endian+"4L",key)
    delta,mask = 0x9e3779b9,0xffffffff
    sum = (delta * n) & mask
    for round in range(n):
        v1 = (v1 - (((v0<<4 ^ v0>>5) + v0) ^ (sum + k[sum>>11 & 3]))) & mask
        sum = (sum - delta) & mask
        v0 = (v0 - (((v1<<4 ^ v1>>5) + v1) ^ (sum + k[sum & 3]))) & mask
    if PY3:
        return struct.pack(endian+"2L",v0,v1).decode('Latin1')
    else:
        return struct.pack(endian+"2L",v0,v1)

if __name__ == "__main__":
    import doctest
    doctest.testmod()
