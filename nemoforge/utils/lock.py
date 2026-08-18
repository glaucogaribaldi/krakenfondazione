import os
import sys
import fcntl

def acquire_lock(lock_path="/tmp/nemoloop.lock"):
    """
    Acquires an exclusive, non-blocking lock on the specified file using fcntl.flock.
    If the lock is already held by another process, exits immediately with code 1.
    Since the lock is linked to the file descriptor managed by the OS kernel,
    it is automatically released if the process crashes or exits.
    """
    try:
        # Open or create the lock file
        # We store the file object in a global variable to prevent it from being garbage collected
        global _lock_file
        _lock_file = open(lock_path, 'w')
        
        # Try to acquire an exclusive lock without blocking
        fcntl.flock(_lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        
        # Write the current process PID to the lock file for diagnostic visibility
        _lock_file.write(str(os.getpid()))
        _lock_file.flush()
        print(f"SUCCESS: Exclusive lock acquired on {lock_path} (PID: {os.getpid()})")
        return True
    except BlockingIOError:
        print(f"ERROR: Another instance of the loop is already running and holding the lock on {lock_path}!")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to acquire lock: {e}")
        sys.exit(1)
