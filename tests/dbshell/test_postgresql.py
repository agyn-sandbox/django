import os
import signal
from unittest import mock

from django.db.backends.postgresql.client import DatabaseClient
from django.test import SimpleTestCase


class PostgreSqlDbshellCommandTestCase(SimpleTestCase):

    def _run_it(self, dbinfo):
        """
        Invoke the runshell command while mocking subprocess.run.
        Returns a 4-tuple containing:
        - The command arguments list
        - The environment dict passed to subprocess.run
        - The pre-call value of os.environ['PGPASSWORD'] (or a sentinel)
        - The post-call value of os.environ['PGPASSWORD'] (or a sentinel)
        """

        sentinel = object()
        original_pgpassword = os.environ.get('PGPASSWORD', sentinel)

        def _mock_subprocess_run(*args, **kwargs):
            self.subprocess_args = list(args[0])
            self.subprocess_env = kwargs['env']
            self.subprocess_kwargs = kwargs
            return mock.Mock(returncode=0)

        self.subprocess_args = None
        self.subprocess_env = None
        self.subprocess_kwargs = None

        with mock.patch('subprocess.run', side_effect=_mock_subprocess_run):
            DatabaseClient.runshell_db(dbinfo)

        current_pgpassword = os.environ.get('PGPASSWORD', sentinel)
        return (
            self.subprocess_args,
            self.subprocess_env,
            original_pgpassword,
            current_pgpassword,
        )

    def test_basic(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            args, env, original, current = self._run_it({
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
        self.assertIn('PGPASSWORD', env)
        self.assertEqual(env['PGPASSWORD'], 'somepassword')
        self.assertNotIn('PGPASSFILE', env)
        self.assertIs(original, current)
        self.assertIsNot(env, os.environ)
        self.assertTrue(self.subprocess_kwargs['check'])

    def test_nopass(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            args, env, original, current = self._run_it({
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
        self.assertIs(original, current)

    def test_column(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            args, env, original, current = self._run_it({
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
        self.assertEqual(env['PGPASSWORD'], 'some:password')
        self.assertIs(original, current)

    def test_escape_characters(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            args, env, original, current = self._run_it({
                'database': 'dbname',
                'user': 'some\\user',
                'password': 'some\\password',
                'host': 'somehost',
                'port': '444',
            })

        self.assertEqual(
            args,
            ['psql', '-U', 'some\\user', '-h', 'somehost', '-p', '444', 'dbname'],
        )
        self.assertEqual(env['PGPASSWORD'], 'some\\password')
        self.assertIs(original, current)

    def test_accent(self):
        username = 'rôle'
        password = 'sésame'
        with mock.patch.dict(os.environ, {}, clear=True):
            args, env, original, current = self._run_it({
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
        self.assertEqual(env['PGPASSWORD'], password)
        self.assertIs(original, current)

    def test_preserve_existing_pgpassword_when_missing(self):
        with mock.patch.dict(os.environ, {'PGPASSWORD': 'from-env'}, clear=True):
            args, env, original, current = self._run_it({
                'database': 'dbname',
            })

        self.assertEqual(args, ['psql', 'dbname'])
        self.assertEqual(env['PGPASSWORD'], 'from-env')
        self.assertEqual(original, 'from-env')
        self.assertEqual(current, 'from-env')

    def test_sigint_handler(self):
        """SIGINT is ignored in Python and passed to psql to abort queries."""

        def _mock_subprocess_run(*args, **kwargs):
            handler = signal.getsignal(signal.SIGINT)
            self.assertEqual(handler, signal.SIG_IGN)
            return mock.Mock(returncode=0)

        sigint_handler = signal.getsignal(signal.SIGINT)
        # The default handler isn't SIG_IGN.
        self.assertNotEqual(sigint_handler, signal.SIG_IGN)
        with mock.patch('subprocess.run', new=_mock_subprocess_run):
            DatabaseClient.runshell_db({})
        # dbshell restores the original handler.
        self.assertEqual(sigint_handler, signal.getsignal(signal.SIGINT))
