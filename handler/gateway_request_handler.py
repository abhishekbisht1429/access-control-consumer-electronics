import logging
import secrets
import shelve
import time
from http import HTTPStatus

import util
from constants import DELTA_T, N, N_BYTES, EC_POINT_G
from cs_config import s_l, SID_l
from ec import ECPoint
from ta import ID_t, f


def handle_msg1(data):
    MG1 = util.deserialize_obj(data)
    C_bytes = MG1['C_bytes']
    C = ECPoint.deserialize(C_bytes)
    T1 = MG1['T1']
    TID_j_bytes = MG1['TID_j_bytes']
    TID_j = int.from_bytes(TID_j_bytes, 'big')
    D = MG1['D']

    # check freshness of TS1
    if time.time_ns() - int.from_bytes(T1, 'big') > DELTA_T:
        logging.error('outdated TS1')
        return HTTPStatus.BAD_REQUEST, None

    with shelve.open('tmp/gn_store') as gn_store:
        if TID_j != gn_store['TID']:
            logging.error('TID_j mismatch')
            return HTTPStatus.BAD_REQUEST, None
        SID_j = gn_store['SID']

    D_dash = util.hash(C_bytes, TID_j_bytes, SID_j, T1)
    if D_dash != D:
        logging.error('D not equal to D_dash')
        return HTTPStatus.BAD_REQUEST, None

    # Puzzle
    PZ1 = SID_j
    PS1 = PZ1[-128:]

    r1 = secrets.randbelow(N)
    r1_bytes = r1.to_bytes(N_BYTES, 'big')
    T2 = util.time_stamp()

    s_l_bytes = s_l.to_bytes(N_BYTES, 'big')
    ID_t_bytes = ID_t.to_bytes(N_BYTES, 'big')
    e1_bytes = util.hash(r1_bytes, s_l_bytes, SID_l, T2, ID_t_bytes)
    e1 = int.from_bytes(e1_bytes, 'big')
    E = EC_POINT_G * e1
    E_bytes = ECPoint.serialize(E)

    DH_lj = C * e1
    DH_lj_bytes = ECPoint.serialize(DH_lj)

    SK_lj = util.hash(DH_lj_bytes, f(SID_l, SID_j), PS1, T2, T1)
    PZ1_star = util.xor(PZ1, util.hash(SID_j, TID_j_bytes, T2, T1))
    SID_l_star = util.xor(SID_l, util.hash(SID_j, PS1, PZ1, T2, T1))

    # select TID_j_n
    TID_j_n = secrets.randbelow(N)
    TID_j_n_bytes = TID_j_n.to_bytes(N_BYTES, 'big')

    TID_j_star_bytes = util.xor(TID_j_n_bytes,
                                util.hash(SK_lj, TID_j_bytes, T2, T1))
    SKV = util.hash(SK_lj, PZ1_star, E_bytes,
                    TID_j_star_bytes, SID_l_star, T2)
    MG2 = {
        'E_bytes': E_bytes,
        'PZ1_star': PZ1_star,
        'SID_l_star': SID_l_star,
        'SKV': SKV,
        'T2': T2,
        'TID_j_star_bytes': TID_j_star_bytes
    }

    # save data required to process ack
    with shelve.open('tmp/cs_store') as cs_store:
        cs_store['SK_lj'] = SK_lj
        cs_store['PS1'] = PS1
        cs_store['PZ1'] = PZ1
        cs_store['T2'] = T2
        cs_store['TID_j_n'] = TID_j_n

    return HTTPStatus.OK, util.serialize_obj(MG2)


def handle_ack(data):
    MG3 = util.deserialize_obj(data)
    Ack = MG3['Ack']
    T3 = MG3['T3']

    if time.time_ns() - int.from_bytes(T3, 'big') > DELTA_T:
        logging.error('Outdated Ack')
        return HTTPStatus.BAD_REQUEST, b'outdated ack'

    with shelve.open('tmp/cs_store') as cs_store:
        SK_lj = cs_store['SK_lj']
        PS1 = cs_store['PS1']
        PZ1 = cs_store['PZ1']
        T2 = cs_store['T2']
        TID_j_n = cs_store['TID_j_n']

    Ack_dash = util.hash(SK_lj, PS1, PZ1, T3, T2)

    if Ack != Ack_dash:
        logging.error('Ack mismatch')
        return HTTPStatus.BAD_REQUEST, b'ack mismatch'

    # update TID_j
    with shelve.open('tmp/cs_store') as cs_store:
        cs_store['TID'] = TID_j_n

    return HTTPStatus.OK, b'success'

def handle(param, data):
    if param[0] == 'mg1':
        return handle_msg1(data)
    elif param[0] == 'ack':
        return handle_ack(data)
