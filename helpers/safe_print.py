import threading
import sys
import logging
s_print_lock = threading.Lock()

logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')

def s_print(*a, **b):
    """Thread safe print function"""
    with s_print_lock:
        logging.info(*a)
        #print(*a, **b, flush=True)
