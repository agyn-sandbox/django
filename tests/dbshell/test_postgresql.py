import os
import signal
import subprocess
from unittest import mock

from django.db.backends.postgresql.client import DatabaseClient
from django.test import SimpleTestCase


class PostgreSqlDbshellCommandTestCase(SimpleTestCase):

    def _run_it(self, dbinfo):
        """
        That function invokes the runshell command, while mocking
        subprocess.run(). It returns a 2-tuple with:
        - The command line list
        - A dict representing the environment passed to subprocess.run().
        """
        def _mock_subprocess_run(*args, env=os.environ, **kwargs):
            self.subprocess_args = list(args[0])
            self.subprocess_env = env.copy()
            return subprocess.CompletedProcess(self.subprocess_args, 0)
        with mock.patch('subprocess.run', new=_mock_subprocess_run):
            DatabaseClient.runshell_db(dbinfo)
        return self.subprocess_args, self.subprocess_env

    def test_basic(self):
        args, env = self._run_it({
            'database': 'dbname',
            'user': 'someuser',
            'password': 'somepassword',
            'host': 'somehost',
            'port': '444',
        })
        self.assertEqual(
            args,
            ['psql', '-U', 'someuser', '-h', 'somehost', '-p', '444', 'dbname'],
        )
        self.assertEqual(env.get('PGPASSWORD'), 'somepassword')
        for key in ('PGSSLMODE', 'PGSSLROOTCERT', 'PGSSLCERT', 'PGSSLKEY'):
            self.assertNotIn(key, env)

    def test_nopass(self):
        args, env = self._run_it({
            'database': 'dbname',
            'user': 'someuser',
            'host': 'somehost',
            'port': '444',
        })
        self.assertEqual(
            args,
            ['psql', '-U', 'someuser', '-h', 'somehost', '-p', '444', 'dbname'],
        )
        self.assertNotIn('PGPASSWORD', env)
        for key in ('PGSSLMODE', 'PGSSLROOTCERT', 'PGSSLCERT', 'PGSSLKEY'):
            self.assertNotIn(key, env)

    def test_column(self):
        args, env = self._run_it({
            'database': 'dbname',
            'user': 'some:user',
            'password': 'some:password',
            'host': '::1',
            'port': '444',
        })
        self.assertEqual(
            args,
            ['psql', '-U', 'some:user', '-h', '::1', '-p', '444', 'dbname'],
        )
        self.assertEqual(env.get('PGPASSWORD'), 'some:password')
        for key in ('PGSSLMODE', 'PGSSLROOTCERT', 'PGSSLCERT', 'PGSSLKEY'):
            self.assertNotIn(key, env)

    def test_accent(self):
        username = 'rôle'
        password = 'sésame'
        args, env = self._run_it({
            'database': 'dbname',
            'user': username,
            'password': password,
            'host': 'somehost',
            'port': '444',
        })
        self.assertEqual(
            args,
            ['psql', '-U', username, '-h', 'somehost', '-p', '444', 'dbname'],
        )
        self.assertEqual(env.get('PGPASSWORD'), password)
        for key in ('PGSSLMODE', 'PGSSLROOTCERT', 'PGSSLCERT', 'PGSSLKEY'):
            self.assertNotIn(key, env)

    def test_ssl_options(self):
        args, env = self._run_it({
            'database': 'dbname',
            'user': 'someuser',
            'password': 'somepassword',
            'host': 'somehost',
            'port': '444',
            'sslmode': 'verify-full',
            'sslrootcert': '/path/to/root.pem',
            'sslcert': '/path/to/client.crt',
            'sslkey': '/path/to/client.key',
        })
        self.assertEqual(
            args,
            ['psql', '-U', 'someuser', '-h', 'somehost', '-p', '444', 'dbname'],
        )
        self.assertEqual(env.get('PGPASSWORD'), 'somepassword')
        self.assertEqual(env.get('PGSSLMODE'), 'verify-full')
        self.assertEqual(env.get('PGSSLROOTCERT'), '/path/to/root.pem')
        self.assertEqual(env.get('PGSSLCERT'), '/path/to/client.crt')
        self.assertEqual(env.get('PGSSLKEY'), '/path/to/client.key')

    def test_partial_ssl_options(self):
        args, env = self._run_it({
            'database': 'dbname',
            'user': 'someuser',
            'host': 'somehost',
            'port': '444',
            'sslmode': 'require',
            'sslkey': '/path/to/client.key',
        })
        self.assertEqual(
            args,
            ['psql', '-U', 'someuser', '-h', 'somehost', '-p', '444', 'dbname'],
        )
        self.assertNotIn('PGPASSWORD', env)
        self.assertEqual(env.get('PGSSLMODE'), 'require')
        self.assertEqual(env.get('PGSSLKEY'), '/path/to/client.key')
        self.assertNotIn('PGSSLROOTCERT', env)
        self.assertNotIn('PGSSLCERT', env)

    def test_without_ssl_options(self):
        args, env = self._run_it({
            'database': 'dbname',
            'user': 'someuser',
            'password': 'somepassword',
            'host': 'somehost',
            'port': '444',
            'sslrootcert': '',
            'sslcert': None,
        })
        self.assertEqual(
            args,
            ['psql', '-U', 'someuser', '-h', 'somehost', '-p', '444', 'dbname'],
        )
        self.assertEqual(env.get('PGPASSWORD'), 'somepassword')
        for key in ('PGSSLMODE', 'PGSSLROOTCERT', 'PGSSLCERT', 'PGSSLKEY'):
            self.assertNotIn(key, env)

    def test_sigint_handler(self):
        """SIGINT is ignored in Python and passed to psql to abort quries."""
        def _mock_subprocess_run(*args, **kwargs):
            handler = signal.getsignal(signal.SIGINT)
            self.assertEqual(handler, signal.SIG_IGN)

        sigint_handler = signal.getsignal(signal.SIGINT)
        # The default handler isn't SIG_IGN.
        self.assertNotEqual(sigint_handler, signal.SIG_IGN)
        with mock.patch('subprocess.run', new=_mock_subprocess_run):
            DatabaseClient.runshell_db({})
        # dbshell restores the original handler.
        self.assertEqual(sigint_handler, signal.getsignal(signal.SIGINT))
