import gateway_config as gn
from constants import N_BITS
import secrets
import shelve
import time

import util
from constants import DELTA_T, EC_POINT_G, N, N_BYTES
from ec import ECPoint
from http import HTTPStatus
import logging


def handle_msg1(data):
    msg1 = util.deserialize_obj(data)

    TID_i_bytes = msg1['TID_bytes']
    Sig_i_bytes = msg1['Sig_bytes']
    A_bytes = msg1['A_bytes']

    TID_i = int.from_bytes(TID_i_bytes, 'big')
    Sig_i = int.from_bytes(Sig_i_bytes, 'big')
    A = ECPoint.deserialize(A_bytes)
    TS1 = msg1['TS1']

    # check freshness of TS1
    TS1_int = int.from_bytes(TS1, 'big')
    current_time = time.time_ns()
    if current_time - TS1_int > DELTA_T:
        logging.error('Request Timeout : ' + str((current_time - TS1_int)))
        return HTTPStatus.REQUEST_TIMEOUT, None

    # in actual case, TID and SID will be delivered to gateway node by TA
    # and gateway node will store them in its database and
    with shelve.open('tmp/sd_store') as sd_store:
        if TID_i != sd_store['TID']:
            return HTTPStatus.BAD_REQUEST, None
        SID_i = sd_store['SID']

    # verify Sig
    # retrive pub_s
    with open('tmp/pub_sd', 'rb') as pub_sd_store:
        pub_s = ECPoint.deserialize(pub_sd_store.read())
    temp = A + pub_s * int.from_bytes(
        util.hash(TID_i_bytes, ECPoint.serialize(A), ECPoint.serialize(pub_s),
                  TS1),
        'big'
    )

    if EC_POINT_G * Sig_i != temp:
        return HTTPStatus.BAD_REQUEST, None

    x2 = secrets.randbelow(N)
    TS2 = util.time_stamp()
    b1_bytes = util.hash(TS2, x2.to_bytes(N_BYTES, 'big'),
                         gn.s.to_bytes(N_BYTES, 'big'),
                         gn.SID
                         )
    b1 = int.from_bytes(b1_bytes, 'big')
    B = EC_POINT_G * b1

    DH_ji = A * b1

    SK_ji = util.hash(ECPoint.serialize(DH_ji), SID_i, TS1,
                      TS2, Sig_i_bytes)

    TID_i_n = secrets.randbits(N_BITS)
    TID_i_n_bytes = TID_i_n.to_bytes(N_BYTES, 'big')
    TID_i_star = util.xor(TID_i_n.to_bytes(N_BYTES, 'big'),
                          util.hash(SK_ji, TID_i_bytes, TS2))

    SKV = util.hash(TID_i_star, SK_ji, ECPoint.serialize(B), TS2, TS1)

    msg2 = {
        'SKV': SKV,
        'TS2': TS2,
        'B_sz': ECPoint.serialize(B),
        'TID_i_star': TID_i_star
    }

    # save data required to process ack
    with shelve.open('tmp/gn_store') as gn_store:
        gn_store['SK_ji'] = SK_ji
        gn_store['TID_i_n_bytes'] = TID_i_n_bytes
        gn_store['TS2'] = TS2

    return HTTPStatus.OK, util.serialize_obj(msg2)


def handle_ack(data):
    msg3 = util.deserialize_obj(data)

    ack = msg3['ack']
    TS3 = msg3['TS3']

    if time.time_ns() - int.from_bytes(TS3, 'big') > DELTA_T:
        logging.error('Outdated request')
        return HTTPStatus.REQUEST_TIMEOUT, None

    with shelve.open('tmp/gn_store') as gn_store:
        SK_ji = gn_store['SK_ji']
        TID_i_n_bytes = gn_store['TID_i_n_bytes']
        TS2 = gn_store['TS2']

        ack_dash = util.hash(SK_ji, TID_i_n_bytes, TS2, TS3)

        if ack != ack_dash:
            logging.error('Ack mismatch')
            return HTTPStatus.BAD_REQUEST, None

        gn_store['TID_i_n'] = TID_i_n_bytes

        return HTTPStatus.OK, b'success'


def handle(param, data):
    if param[0] == 'msg1':
        return handle_msg1(data)
    elif param[0] == 'ack':
        return handle_ack(data)
