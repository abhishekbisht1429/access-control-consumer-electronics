import sys

import cbor2


def inv(x, p):
    """
    Uses Fermat's Little Theorem
    :param x:
    :param p:
    :return: int, inverse of x mod p
    """
    # TODO: use extended euclidian algorithm here
    if x % p == 0:
        raise ZeroDivisionError("Cannot invert")
    return pow(x, p - 2, p)


class ECCurve:
    def __init__(self, p, a, b, g, n, n_bits):
        """
        Constructor
        :param p: int, prime number for mod operations
        :param a: int, linear part coefficient of the curve
        :param b: int, constant part of the curve
        :param g: tuple, a 2D point
        :param n: int, order of the group
        :param n_bits: int, number of bits used to represent p
        """
        self.p = p
        self.a = a
        self.b = b
        self.g = (g[0], g[1])
        self.n = n
        self.n_bits = n_bits

        # zero point
        self.o = (p, 0)

    def __eq__(self, other):
        return (self.p, self.a, self.b, self.g, self.n, self.n_bits) == \
            (other.p, other.a, other.b, other.g, other.n, other.n_bits)

    @classmethod
    def serialize(cls, curve):
        return cbor2.dumps((
            curve.p,
            curve.a,
            curve.b,
            curve.g,
            curve.n,
            curve.n_bits
        ))

    @classmethod
    def deserialize(cls, sz_curve):
        data = cbor2.loads(sz_curve)
        return cls(*data)


class ECPoint:

    def __init__(self, point, curve):
        """
        Constructor
        :param point: tuple, a 2D point
        :param curve: ECCurve, an elliptic curve
        """
        self._point = (point[0], point[1])
        self._curve = curve

        if not self._valid():
            raise ValueError("Invalid points for given curve")

    @property
    def x(self):
        return self._point[0]

    @property
    def y(self):
        return self._point[1]

    @property
    def curve(self):
        return self._curve

    def _valid(self):
        """
        :return: true, if 'point' is valid point of 'curve', false, otherwise
        """
        if self._point == self._curve.o:
            return True
        else:
            x, y = self._point
            a, b, p = self._curve.a, self._curve.b, self._curve.p

            return (0 <= x < self._curve.p) and (0 <= y < self._curve.p) and \
                ((y ** 2 - (x ** 3 + a * x + b)) % p) == 0

    def inv(self):
        """
        :return: inverse of this ECPoint
        """
        if self._point == self._curve.o:
            return self
        return ECPoint((self._point[0], (-self._point[1]) % self._curve.p),
                       self._curve)

    def __eq__(self, other):
        """
        :param other: ECPoint
        :return:
        """
        return (self._point == other._point) and (self._curve == other._curve)

    def __add__(self, other):
        """
        :param other: ECPoint
        :return: addition of 'self' and 'other' ECPoint
        """
        if other._curve != self._curve:
            raise ValueError("Invalid Input")

        if self._point == self._curve.o:
            return other
        elif other._point == other._curve.o:
            return self
        elif self.inv() == other:
            return ECPoint(self._curve.o, self._curve)

        x1, y1 = self._point
        x2, y2 = other._point
        a, p = self._curve.a, self._curve.p

        if self == other:
            delta = ((3 * x1 ** 2 + a) * inv(2 * y1, p)) % p
        else:
            delta = ((y2 - y1) * inv(x2 - x1, p)) % p

        x = (delta ** 2 - x1 - x2) % p
        y = (delta * (x1 - x) - y1) % p

        return ECPoint((x, y), self._curve)

    def __mul__(self, scalar):
        """
        Scalar multiplication
        :param scalar: int, a scalar
        :return:
        """
        if not isinstance(scalar, int):
            raise TypeError("other must of type int")

        res = ECPoint(self._curve.o, self._curve)
        temp = self
        while scalar != 0:
            if scalar & 1:
                res = res + temp
            scalar >>= 1

            if scalar != 0:
                temp = temp + temp

        return res

    def __str__(self):
        return str(self._point)

    @classmethod
    def serialize(cls, point):
        return cbor2.dumps((
            (point.x, point.y),
            ECCurve.serialize(point.curve)
        ))

    @classmethod
    def deserialize(cls, sz_point):
        point, sz_curve = cbor2.loads(sz_point)
        return cls(point, ECCurve.deserialize(sz_curve))


if __name__ == "__main__":
    p = 0xffffffff00000001000000000000000000000000ffffffffffffffffffffffff
    a = 0xffffffff00000001000000000000000000000000fffffffffffffffffffffffc
    b = 0x5ac635d8aa3a93e7b3ebbd55769886bc651d06b0cc53b0f63bce3c3e27d2604b
    g = (0x6b17d1f2e12c4247f8bce6e563a440f277037d812deb33a0f4a13945d898c296,
         0x4fe342e2fe1a7f9b8ee7eb4a7c0f9e162bce33576b315ececbb6406837bf51f5)
    n = 0xffffffff00000000ffffffffffffffffbce6faada7179e84f3b9cac2fc632551
    n_bits = 256

    secp256r1 = ECCurve(p, a, b, g, n, n_bits)

    generator = ECPoint(g, secp256r1)
    print("generator: ", generator)

    p = generator * 2
    print("p: ", p)
    q = generator * 4
    print("q: ", q)
    r = generator * 1024
    print("r: ", r)

    two_p = p + p
    three_p = two_p + p

    assert ((p + three_p) == (two_p + two_p))
    assert ((p + (q + r)) == ((p + q) + r))

    sz_p = ECPoint.serialize(p)
    assert(p == ECPoint.deserialize(sz_p))
