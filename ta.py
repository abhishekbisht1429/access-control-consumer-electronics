import secrets
import shelve

from constants import N_BITS, N, N_BYTES

with (shelve.open('tmp/ta') as ta_store):
    if 'ID_t' not in ta_store:
        ta_store['ID_t'] = secrets.randbits(N_BITS)
        ta_store['m_t'] = secrets.randbelow(N)
        ta_store['t'] = 20
        ta_store['coeffs'] = \
            [secrets.randbelow(N) for _ in range(ta_store['t'])]

    ID_t = ta_store['ID_t']
    m_t = ta_store['m_t']
    t = ta_store['t']
    coeffs = ta_store['coeffs']


def f(x_bytes, y_bytes):
    x = int.from_bytes(x_bytes, 'big')
    y = int.from_bytes(y_bytes, 'big')
    res = 0
    for u in range(0, t):
        for v in range(0, t):
            res += (x ** u) * (y ** v)
    res %= N

    return res.to_bytes(N_BYTES, 'big')

