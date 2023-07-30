# ECC constants

# secp256r1
from ec import ECCurve, ECPoint

Q = 0xffffffff00000001000000000000000000000000ffffffffffffffffffffffff
A = 0xffffffff00000001000000000000000000000000fffffffffffffffffffffffc
B = 0x5ac635d8aa3a93e7b3ebbd55769886bc651d06b0cc53b0f63bce3c3e27d2604b
G = (0x6b17d1f2e12c4247f8bce6e563a440f277037d812deb33a0f4a13945d898c296,
     0x4fe342e2fe1a7f9b8ee7eb4a7c0f9e162bce33576b315ececbb6406837bf51f5)
N = 0xffffffff00000000ffffffffffffffffbce6faada7179e84f3b9cac2fc632551
N_BITS = 256
N_BYTES = N_BITS // 8

EC_CURVE_SECP256R1 = ECCurve(Q, A, B, G, N, N_BITS)

EC_POINT_G = ECPoint(G, EC_CURVE_SECP256R1)

DELTA_T = 2000000000

