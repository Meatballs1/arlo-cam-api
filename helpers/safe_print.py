import threading
import sys
s_print_lock = threading.Lock()

def s_print(*a, **b):
    """Thread safe print function"""
    with s_print_lock:
        print(*a, **b, flush=True)
