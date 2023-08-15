import json
import os
import secrets
import shelve
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib import parse

import requests

import util
from constants import N, N_BYTES, EC_POINT_G, DELTA_T
from ec import ECPoint
from handler import sd_request_handler
from gateway_config import config, logging, SID_j, s_j, TID_j, CS_MG1_URL, \
    CS_ACK_URL
from ta import f


class ServerRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        # Split path into its components
        path = parse.urlparse(self.path).path
        path_components = path.split(os.path.sep)
        # print("get: ", path_components)

        # check if appropriate number of parameters have been provided
        if len(path_components) < 2:
            self.send_error(404)
            self.end_headers()
            return

        # headers
        # print(self.headers.keys())
        content_len = self.headers.get('Content-Length')
        if content_len is None:
            self.send_error(411)
            self.end_headers()
            return
        content_len = int(content_len)

        # delegate the task to appropriate handler
        res_body = None
        data = None
        if content_len > 0:
            data = self.rfile.read(content_len)
        if path_components[1] == "gateway_node":
            res_code, res_body = sd_request_handler.handle(path_components[2:],
                                                           data)

        # return response to the server
        self.send_response(res_code, self.responses[res_code][0])
        self.end_headers()

        if res_code == 200:
            self.wfile.write(res_body)

def establish_cs_key():
    TID_j_bytes = TID_j.to_bytes(N_BYTES, 'big')

    y1 = secrets.randbelow(N)
    y1_bytes = y1.to_bytes(N_BYTES, 'big')
    T1 = util.time_stamp()

    s_j_bytes = s_j.to_bytes(N_BYTES, 'big')
    c1_bytes = util.hash(y1_bytes, T1, SID_j, s_j_bytes, TID_j_bytes)
    c1 = int.from_bytes(c1_bytes, 'big')
    C = EC_POINT_G * c1
    C_bytes = ECPoint.serialize(C)
    D = util.hash(C_bytes, TID_j_bytes, SID_j, T1)

    MG1 = {
        'C_bytes': C_bytes,
        'T1': T1,
        'TID_j_bytes': TID_j_bytes,
        'D': D
    }

    print('=================== Sending MG1 ========================>>>')
    print('C')
    print('T1')
    print('TID_j')
    print('D')
    print('===========================================================')

    print(CS_MG1_URL)
    print(CS_ACK_URL)
    response = requests.post(CS_MG1_URL, util.serialize_obj(MG1))
    if response.status_code != HTTPStatus.OK:
        logging.error('error during sending MG1' + str(response.status_code))
        return

    MG2 = util.deserialize_obj(response.text)

    E_bytes = MG2['E_bytes']
    E = ECPoint.deserialize(E_bytes)
    PZ1_star = MG2['PZ1_star']
    SID_l_star = MG2['SID_l_star']
    SKV = MG2['SKV']
    T2 = MG2['T2']
    TID_j_star_bytes = MG2['TID_j_star_bytes']

    print('<<<================= Receiving MG2 =========================')
    print('E')
    print('PZ1_star')
    print('SID_l_star')
    print('SKV')
    print('T2')
    print('TID_j_star')
    print('============================================================')

    if time.time_ns() - int.from_bytes(T2, 'big') > DELTA_T:
        logging.error('Outdated T2')
        return
    PZ1 = util.xor(PZ1_star, util.hash(SID_j, TID_j_bytes, T2, T1))
    PS1_dash = PZ1[-128:]

    SID_l = util.xor(SID_l_star, util.hash(SID_j, PS1_dash, PZ1, T2, T1))
    DH_jl = E * c1
    DH_jl_bytes = ECPoint.serialize(DH_jl)
    SK_jl = util.hash(DH_jl_bytes, f(SID_j, SID_l), PS1_dash, T2, T1)
    TID_j_n_bytes = util.xor(TID_j_star_bytes,
                             util.hash(SK_jl, SID_j, TID_j_bytes,
                                                         T2, T1))

    SKV_dash = util.hash(SK_jl, PZ1_star, E_bytes, TID_j_star_bytes,
                         SID_l_star, T2)

    if SKV_dash != SKV:
        logging.error("SKV and SKV_dash mismatch")
        return

    TID_j_n = int.from_bytes(TID_j_n_bytes, 'big')

    with shelve.open('tmp/gn_store') as gn_store:
        gn_store['TID'] = TID_j_n

    T3 = util.time_stamp()

    Ack = util.hash(SK_jl, PS1_dash, PZ1, T3, T2)

    MG3 = {
        'Ack': Ack,
        'T3': T3
    }

    print('=================== Sending MG3 =============================>>>')
    print('Ack')
    print('T3')
    print('================================================================')

    response = requests.post(CS_ACK_URL, util.serialize_obj(MG3))

    if response.status_code != HTTPStatus.OK:
        logging.error('Ack failed to deliver')
        return

    print('Shared Session Key : ', SK_jl)


if __name__ == '__main__':
    addr = (config['server_ip'], config['server_port'])
    server = HTTPServer(addr, ServerRequestHandler)
    logging.info("serving requests from %s", addr)
    server.serve_forever()

    # establish_cs_key()