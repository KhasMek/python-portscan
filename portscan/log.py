import logging
import datetime
import os
import time

__all__ = [
    'send_log'
]

LOG_FILE = "/var/log/python-portscan/log"
if not os.path.exists(os.path.dirname(LOG_FILE)):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
open(LOG_FILE, 'a').close()
logging.basicConfig(filename=LOG_FILE, level=logging.INFO)


def send_log(message):
    """Logging method used throughout python-portscan"""
    logging.info(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S') + " " + message)
