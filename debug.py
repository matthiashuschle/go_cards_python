import os
import logging
import time
from contextlib import contextmanager


@contextmanager
def log_time(msg):
    start = time.time()
    yield
    logging.debug('elapsed: %.03f msg: %s' % (time.time() - start, msg))


def setup_logging(dir):
    logging.basicConfig(filename=os.path.join(dir, 'debug.log'), level=logging.DEBUG)
