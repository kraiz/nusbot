import configparser
import logging
import os


logger = logging.getLogger(__name__)


DEFAULT_CONFIG = """[DEFAULT]
hub_host = 192.168.0.2
hub_port = 1511
nickname = nusbot
filelist_update = 5m
"""

config_dir = os.path.expanduser(os.path.join('~', '.nusbot'))

from datetime import timedelta

def convert_to_timedelta(time_val):
    num = int(time_val[:-1])
    if time_val.endswith('s'):
        return timedelta(seconds=num)
    elif time_val.endswith('m'):
        return timedelta(minutes=num)
    elif time_val.endswith('h'):
        return timedelta(hours=num)
    elif time_val.endswith('d'):
        return timedelta(days=num)
    elif time_val.endswith('w'):
        return timedelta(weeks=num)
    elif time_val.endswith('y'):
        return timedelta(days=365*num)

def format_bytes(num):
    for x in ['B','KB','MB','GB','TB', 'PT']:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0

def _get_config():
    config = configparser.ConfigParser()

    if not os.path.exists(config_dir):
        os.mkdir(config_dir)

    config_file = os.path.join(config_dir, 'config.ini')
    if not os.path.exists(config_file):
        logger.warn('No config found. Writing default to %s - change it!')
        with open(config_file, 'w') as f:
            f.write(DEFAULT_CONFIG)

    config.read(config_file)
    return config['DEFAULT']


config = _get_config()
