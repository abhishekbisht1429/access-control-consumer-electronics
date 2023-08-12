import logging
import os
import secrets
import shelve

import yaml

import util
from constants import N, N_BITS, N_BYTES, EC_POINT_G
from ec import ECPoint
from ta import m_t

logging.basicConfig(level=logging.INFO)

with open('cs_config.yml') as config_file:
    config = yaml.safe_load(config_file)

with shelve.open('tmp/cs_store') as gn_store:
    if 'ID' not in gn_store:
        gn_store['ID'] = secrets.randbits(N_BITS)

    ID = gn_store['ID']

    if 'TID' not in gn_store:
        gn_store['TID'] = secrets.randbits(N_BITS)
        gn_store['RTS'] = util.time_stamp()
        gn_store['SID'] = util.hash(
            ID.to_bytes(N_BYTES, 'big'),
            gn_store['TID'].to_bytes(N_BYTES, 'big'),
            gn_store['RTS'],
            m_t.to_bytes(N_BYTES, 'big'),
        )

    TID_l = gn_store['TID']
    RTS = gn_store['RTS']
    SID_l = gn_store['SID']

    if 's' not in gn_store:
        gn_store['s'] = secrets.randbelow(N)
    s_l = gn_store['s']

    pub_s = EC_POINT_G * s_l
    with open('tmp/gn_pub', 'wb') as pub_s_store:
        pub_s_store.write(ECPoint.serialize(pub_s))
