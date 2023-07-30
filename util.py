import base64
import math
import time

import cbor2
from cryptography.hazmat.primitives import hashes


def hash(*args):
    digest = hashes.Hash(hashes.SHA256())
    for arg in args:
        digest.update(arg)
    return digest.finalize()


def xor(*args):
    args = list(args)
    # append zeros at front to make length of all bytes object equal
    max_len = 0
    for arg in args:
        max_len = max(max_len, len(arg))

    for i in range(len(args)):
        len_arg = len(args[i])
        if len_arg != max_len:
            args[i] = bytearray(max_len - len_arg) + args[i]
    res = []
    for x in zip(*args):
        r = 0
        for b in x:
            r = r ^ b
        res.append(r)

    return bytes(res)


def byte_len(val):
    return int(math.ceil(val.bit_length() / 8))


def time_stamp():
    time_int = time.time_ns()
    return time_int.to_bytes(8, 'big')


def bytes_to_base64s(data) -> str:
    """

    :param data, bytes:
    :return:
    """

    return base64.b64encode(data).decode('utf-8')


def b64s_to_bytes(s):
    """
    converts a base64 string to bytes
    :param s:
    :return:
    """
    return base64.b64decode(s.encode('utf-8'))


def serialize_obj(obj):
    return base64.b64encode(cbor2.dumps(obj))


def deserialize_obj(data):
    return cbor2.loads(base64.b64decode(data))

#
# if __name__ == '__main__':
#     print(xor(b'asfd', b'sdfasfdasfd', b'asfd'))
