import logging
import secrets
import shelve
import sys
import time
from http import HTTPStatus

import requests
import util

from constants import N, EC_POINT_G, N_BITS, N_BYTES, DELTA_T
from ec import ECPoint
from sd_config import GN_ACK_URL, GN_MSG1_URL
from ta import ID_t, m_t


with shelve.open('tmp/sd_store') as sd_store:
    if 'ID' not in sd_store:
        sd_store['ID'] = secrets.randbits(N_BITS)
        sd_store['TID'] = secrets.randbits(N_BITS)
        sd_store['RTS'] = util.time_stamp()
        sd_store['SID'] = util.hash(
            sd_store['ID'].to_bytes(N_BYTES, 'big'),
            sd_store['TID'].to_bytes(N_BYTES, 'big'),
            sd_store['RTS'],
            m_t.to_bytes(N_BYTES, 'big'),
            ID_t.to_bytes(N_BYTES, 'big')
        )
        sd_store['s'] = secrets.randbelow(N)

    ID = sd_store['ID']
    TID_i = sd_store['TID']
    RTS = sd_store['RTS']
    SID_i = sd_store['SID']
    s = sd_store['s']
    pub_s = EC_POINT_G * s
    with open('tmp/pub_sd', 'wb') as pub_s_store:
        pub_s_store.write(ECPoint.serialize(pub_s))


def init_access_control():
    x = secrets.randbelow(N)
    TS1 = util.time_stamp()
    a1 = int.from_bytes(util.hash(
        s.to_bytes(N_BYTES, 'big'),
        x.to_bytes(N_BYTES, 'big'),
        TS1,
        SID_i,
        TID_i.to_bytes(N_BYTES, 'big')
    ), 'big')
    A = EC_POINT_G * a1
    Sig = (a1 + int.from_bytes(
        util.hash(
            TID_i.to_bytes(N_BYTES, 'big'),
            ECPoint.serialize(A),
            ECPoint.serialize(pub_s),
            TS1
        ), 'big') * s) % N

    # send msg1 to Gateway Node
    Sig_i_bytes = Sig.to_bytes(N_BYTES, 'big')
    TID_i_bytes = TID_i.to_bytes(N_BYTES, 'big')
    msg1 = {
        'TID_bytes': TID_i_bytes,
        'Sig_bytes': Sig_i_bytes,
        'A_bytes': ECPoint.serialize(A),
        'TS1': TS1
    }

    # send request to gateway node
    response = requests.post(GN_MSG1_URL, util.serialize_obj(msg1))
    logging.info('response code : ' + str(response.status_code))
    msg2 = util.deserialize_obj(response.text)
    print('message ', util.deserialize_obj(response.text))
    SKV = msg2['SKV']
    TS2 = msg2['TS2']
    B_sz = msg2['B_sz']
    TID_i_star = msg2['TID_i_star']

    B = ECPoint.deserialize(B_sz)

    # check freshness of TS2
    if time.time_ns() - int.from_bytes(TS2, 'big') > DELTA_T:
        logging.error('Outdated response')
        return

    DH_ji = B * a1
    SK_ij = util.hash(ECPoint.serialize(DH_ji), SID_i, TS1, TS2,
                      Sig_i_bytes)
    TID_i_n_bytes = util.xor(TID_i_star,
                       util.hash(SK_ij, TID_i_bytes, TS2))
    TID_i_n = int.from_bytes(TID_i_n_bytes, 'big')
    SKV_dash = util.hash(TID_i_star, SK_ij, ECPoint.serialize(B), TS2,
                         TS1)
    if SKV_dash != SKV:
        logging.error('SKV mismatch')
        return

    TS3 = util.time_stamp()

    # update TID_i
    with shelve.open('tmp/sd_store') as sd_store:
        sd_store['TID'] = TID_i_n

    # calculate ack
    ack = util.hash(SK_ij, TID_i_n_bytes, TS2, TS3)

    # send ack and ts3 to gateway_node
    msg3 = {
        'ack': ack,
        'TS3': TS3
    }

    response = requests.post(GN_ACK_URL, util.serialize_obj(msg3))

    if response.status_code != HTTPStatus.OK:
        logging.error('Error while sending ack')
        return
    logging.info('Ack sent')








if __name__ == '__main__':
    init_access_control()
