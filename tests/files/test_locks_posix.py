import os
import tempfile
import unittest

from django.core.files import locks

try:
    import fcntl  # noqa: F401
except ImportError:  # pragma: no cover - platform dependent
    fcntl = None


def _tempfile_path():
    temp = tempfile.NamedTemporaryFile(delete=False)
    try:
        return temp.name
    finally:
        temp.close()


@unittest.skipIf(os.name == 'nt', 'POSIX only')
@unittest.skipUnless(fcntl, 'fcntl unavailable')
class PosixLockTests(unittest.TestCase):

    def test_exclusive_lock_and_unlock_return_true(self):
        path = _tempfile_path()
        self.addCleanup(lambda: os.unlink(path))
        with open(path, 'w+') as handler:
            self.assertTrue(locks.lock(handler, locks.LOCK_EX))
            self.assertTrue(locks.unlock(handler))

    def test_shared_lock_and_unlock_return_true(self):
        path = _tempfile_path()
        self.addCleanup(lambda: os.unlink(path))
        with open(path, 'w+') as handler:
            self.assertTrue(locks.lock(handler, locks.LOCK_SH))
            self.assertTrue(locks.unlock(handler))

    def test_non_blocking_exclusive_conflict_returns_false(self):
        path = _tempfile_path()
        self.addCleanup(lambda: os.unlink(path))
        with open(path, 'w+') as first, open(path, 'r+') as second:
            self.assertTrue(locks.lock(first, locks.LOCK_EX))
            try:
                self.assertFalse(
                    locks.lock(second, locks.LOCK_EX | locks.LOCK_NB)
                )
            finally:
                self.assertTrue(locks.unlock(first))

        with open(path, 'r+') as second:
            self.assertTrue(locks.lock(second, locks.LOCK_EX))
            self.assertTrue(locks.unlock(second))
