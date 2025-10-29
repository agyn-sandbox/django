import os
import subprocess
import signal
from unittest import mock

from django.db.backends.postgresql.client import DatabaseClient
from django.test import SimpleTestCase


class PostgreSqlDbshellCommandTestCase(SimpleTestCase):

    def _run_it(self, dbinfo):
        """
        That function invokes the runshell command, while mocking
        subprocess.run. It returns a 2-tuple with:
        - The command line list
        - The PGPASSWORD value from the env passed to subprocess.run, or None.
        """
        def _mock_subprocess_run(*args, **kwargs):
            self.subprocess_args = list(*args)
            env = kwargs.get('env') or {}
            self.pgpassword = env.get('PGPASSWORD')
            # Capture check=True
            self.assertTrue(kwargs.get('check'))
            # Ensure PGPASSFILE not passed in env
            self.assertNotIn('PGPASSFILE', env)
            class Result:
                returncode = 0
            return Result()
        self.subprocess_args = None
        self.pgpassword = None
        with mock.patch('subprocess.run', new=_mock_subprocess_run):
            DatabaseClient.runshell_db(dbinfo)
        return self.subprocess_args, self.pgpassword

    def test_basic(self):
        self.assertEqual(
            self._run_it({
                'database': 'dbname',
                'user': 'someuser',
                'password': 'somepassword',
                'host': 'somehost',
                'port': '444',
            }), (
                ['psql', '-U', 'someuser', '-h', 'somehost', '-p', '444', 'dbname'],
                'somepassword',
            )
        )

    def test_nopass(self):
        self.assertEqual(
            self._run_it({
                'database': 'dbname',
                'user': 'someuser',
                'host': 'somehost',
                'port': '444',
            }), (
                ['psql', '-U', 'someuser', '-h', 'somehost', '-p', '444', 'dbname'],
                None,
            )
        )

    def test_column(self):
        self.assertEqual(
            self._run_it({
                'database': 'dbname',
                'user': 'some:user',
                'password': 'some:password',
                'host': '::1',
                'port': '444',
            }), (
                ['psql', '-U', 'some:user', '-h', '::1', '-p', '444', 'dbname'],
                'some:password',
            )
        )

    def test_escape_characters(self):
        self.assertEqual(
            self._run_it({
                'database': 'dbname',
                'user': 'some\\user',
                'password': 'some\\password',
                'host': 'somehost',
                'port': '444',
            }), (
                ['psql', '-U', 'some\\user', '-h', 'somehost', '-p', '444', 'dbname'],
                'some\\password',
            )
        )

    def test_accent(self):
        username = 'rôle'
        password = 'sésame'
        pgpassword_string = password
        self.assertEqual(
            self._run_it({
                'database': 'dbname',
                'user': username,
                'password': password,
                'host': 'somehost',
                'port': '444',
            }), (
                ['psql', '-U', username, '-h', 'somehost', '-p', '444', 'dbname'],
                pgpassword_string,
            )
        )

    def test_sigint_handler(self):
        """SIGINT is ignored in Python and passed to psql to abort queries."""
        def _mock_subprocess_run(*args, **kwargs):
            handler = signal.getsignal(signal.SIGINT)
            self.assertEqual(handler, signal.SIG_IGN)
            class Result:
                returncode = 0
            return Result()

        sigint_handler = signal.getsignal(signal.SIGINT)
        # The default handler isn't SIG_IGN.
        self.assertNotEqual(sigint_handler, signal.SIG_IGN)
        with mock.patch('subprocess.run', new=_mock_subprocess_run):
            DatabaseClient.runshell_db({})
        # dbshell restores the original handler.
        self.assertEqual(sigint_handler, signal.getsignal(signal.SIGINT))

    def test_env_not_mutated_and_error_restores_sigint(self):
        """Environment is not mutated and SIGINT restored on error."""
        # Ensure PGPASSWORD not in os.environ before call.
        self.assertNotIn('PGPASSWORD', os.environ)

        def _mock_subprocess_run(*args, **kwargs):
            # During the call, ensure SIGINT is ignored.
            self.assertEqual(signal.getsignal(signal.SIGINT), signal.SIG_IGN)
            # The env passed to subprocess.run must not include PGPASSFILE.
            env = kwargs.get('env') or {}
            self.assertNotIn('PGPASSFILE', env)
            # Simulate a failure.
            raise subprocess.CalledProcessError(returncode=1, cmd=kwargs.get('args', []))

        sigint_handler = signal.getsignal(signal.SIGINT)
        with mock.patch('subprocess.run', new=_mock_subprocess_run):
            with self.assertRaises(subprocess.CalledProcessError):
                DatabaseClient.runshell_db({
                    'database': 'dbname',
                    'user': 'u',
                    'password': 'p',
                    'host': 'h',
                    'port': '444',
                })
        # After call, original SIGINT handler restored and os.environ unchanged.
        self.assertEqual(sigint_handler, signal.getsignal(signal.SIGINT))
        self.assertNotIn('PGPASSWORD', os.environ)
