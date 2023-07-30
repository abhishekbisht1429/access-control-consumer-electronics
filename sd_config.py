import logging
import os
import secrets
import shelve

import yaml

import util
from constants import N_BITS, N_BYTES, EC_POINT_G, N
from ec import ECPoint
from ta import ID_t, m_t

logging.basicConfig(level=logging.INFO)

with open('sd_config.yml') as config_file:
    config = yaml.safe_load(config_file)

GATEWAY_NODE_URL = config['url']['gateway_node']['base']
GN_MSG1_URL = GATEWAY_NODE_URL + '/' + 'msg1'
GN_ACK_URL = GATEWAY_NODE_URL + '/' + 'ack'
