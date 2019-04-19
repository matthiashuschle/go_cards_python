import time
import datetime
from contextlib import contextmanager
from queue import Queue
from threading import Thread

_LOG_THREAD = None
_LOG_QUEUE = Queue()


@contextmanager
def log_time(msg):
    start = time.time()
    yield
    log_msg('elapsed: %.03f msg: %s' % (time.time() - start, msg))


def log_msg(msg):
    _LOG_QUEUE.put(msg)


def setup_logging(log_path):
    global _LOG_THREAD
    if _LOG_THREAD is not None:
        return
    _LOG_THREAD = Thread(target=log_loop, args=[log_path], daemon=True)
    _LOG_THREAD.start()


def log_loop(log_path):
    with open(log_path, 'w') as logfile:
        while True:
            entry = _LOG_QUEUE.get(block=True)
            timestamp = datetime.datetime.now().isoformat()[:19]
            logfile.write('%s: %s\n' % (timestamp, entry))
            logfile.flush()
