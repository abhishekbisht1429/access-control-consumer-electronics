import logging
import os
import shelve

import yaml

logging.basicConfig(level=logging.INFO)

with open('gateway_config.yml') as config_file:
    config = yaml.safe_load(config_file)