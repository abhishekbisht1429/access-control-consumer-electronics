import secrets
import shelve

from constants import N_BITS, N

with shelve.open('tmp/ta') as ta_store:
    if 'ID_t' not in ta_store:
        ta_store['ID_t'] = secrets.randbits(N_BITS)
        ta_store['m_t'] = secrets.randbelow(N)

    ID_t = ta_store['ID_t']
    m_t = ta_store['m_t']