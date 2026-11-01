"""_tc/scripts/lock_utils.py
Cross-platform advisory file locking utility supporting POSIX (fcntl.flock) and Windows (msvcrt.locking).
"""
from __future__ import annotations

import contextlib
import os
import sys
import time
from typing import IO, Any

if sys.platform == "win32":
    import msvcrt

    @contextlib.contextmanager
    def file_lock(file_obj: IO[Any], exclusive: bool = True, timeout: float = 15.0):
        """Acquire advisory file lock on Windows using msvcrt."""
        fileno = file_obj.fileno()
        start = time.time()
        try:
            current_pos = file_obj.tell()
        except Exception:
            current_pos = 0

        locked = False
        while not locked:
            try:
                try:
                    file_obj.seek(0)
                except Exception:
                    pass
                msvcrt.locking(fileno, msvcrt.LK_NBLCK, 1)
                locked = True
                try:
                    file_obj.seek(current_pos)
                except Exception:
                    pass
            except OSError:
                if time.time() - start >= timeout:
                    try:
                        msvcrt.locking(fileno, msvcrt.LK_LOCK, 1)
                        locked = True
                    except OSError as err:
                        raise TimeoutError(f"Could not acquire file lock within {timeout}s: {err}") from err
                    break
                time.sleep(0.01)

        try:
            yield
        finally:
            if locked:
                try:
                    cur = file_obj.tell()
                except Exception:
                    cur = 0
                try:
                    file_obj.seek(0)
                    msvcrt.locking(fileno, msvcrt.LK_UNLCK, 1)
                except OSError:
                    pass
                try:
                    file_obj.seek(cur)
                except Exception:
                    pass

    def lock_file(file_obj: IO[Any], exclusive: bool = True, timeout: float = 15.0) -> None:
        fileno = file_obj.fileno()
        start = time.time()
        while True:
            try:
                file_obj.seek(0)
                msvcrt.locking(fileno, msvcrt.LK_NBLCK, 1)
                return
            except OSError:
                if time.time() - start >= timeout:
                    msvcrt.locking(fileno, msvcrt.LK_LOCK, 1)
                    return
                time.sleep(0.01)

    def unlock_file(file_obj: IO[Any]) -> None:
        try:
            file_obj.seek(0)
            msvcrt.locking(file_obj.fileno(), msvcrt.LK_UNLCK, 1)
        except OSError:
            pass

else:
    try:
        import fcntl

        @contextlib.contextmanager
        def file_lock(file_obj: IO[Any], exclusive: bool = True, timeout: float = 15.0):
            """Acquire advisory file lock on POSIX using fcntl.flock."""
            fileno = file_obj.fileno()
            op = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
            fcntl.flock(fileno, op)
            try:
                yield
            finally:
                fcntl.flock(fileno, fcntl.LOCK_UN)

        def lock_file(file_obj: IO[Any], exclusive: bool = True, timeout: float = 15.0) -> None:
            op = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
            fcntl.flock(file_obj.fileno(), op)

        def unlock_file(file_obj: IO[Any]) -> None:
            fcntl.flock(file_obj.fileno(), fcntl.LOCK_UN)

    except ImportError:
        @contextlib.contextmanager
        def file_lock(file_obj: IO[Any], exclusive: bool = True, timeout: float = 15.0):
            yield

        def lock_file(file_obj: IO[Any], exclusive: bool = True, timeout: float = 15.0) -> None:
            pass

        def unlock_file(file_obj: IO[Any]) -> None:
            pass
