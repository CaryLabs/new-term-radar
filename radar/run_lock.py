"""Cross-process OS file lock; released by the OS even after a crash."""
from contextlib import contextmanager
import os
from pathlib import Path


@contextmanager
def hold(state):
    path=Path(state)
    path.mkdir(parents=True,exist_ok=True)
    with (path/'.provider-run.lock').open('a+b') as lock:
        lock.seek(0)
        if os.fstat(lock.fileno()).st_size == 0:
            lock.write(b'0');lock.flush()
        lock.seek(0)
        try:
            if os.name=='nt':
                import msvcrt
                msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError:
            raise ValueError('Another process is using this state directory') from None
        try:yield
        finally:
            lock.seek(0)
            if os.name=='nt':
                msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)
            else:
                fcntl.flock(lock.fileno(),fcntl.LOCK_UN)
