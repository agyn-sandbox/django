import os
import signal
import subprocess

from django.db.backends.base.client import BaseDatabaseClient


class DatabaseClient(BaseDatabaseClient):
    executable_name = 'psql'

    @classmethod
    def runshell_db(cls, conn_params):
        args = [cls.executable_name]

        host = conn_params.get('host', '')
        port = conn_params.get('port', '')
        dbname = conn_params.get('database', '')
        user = conn_params.get('user', '')
        passwd = conn_params.get('password', '')

        if user:
            args += ['-U', user]
        if host:
            args += ['-h', host]
        if port:
            args += ['-p', str(port)]
        args += [dbname]

        sigint_handler = signal.getsignal(signal.SIGINT)
        subprocess_env = os.environ.copy()
        if passwd:
            subprocess_env['PGPASSWORD'] = str(passwd)
        # Map SSL-related connection parameters to libpq environment variables
        # so that psql/libpq can establish mutual TLS when configured.
        ssl_mapping = {
            'sslmode': 'PGSSLMODE',
            'sslrootcert': 'PGSSLROOTCERT',
            'sslcert': 'PGSSLCERT',
            'sslkey': 'PGSSLKEY',
        }
        for opt_key, env_key in ssl_mapping.items():
            opt_val = conn_params.get(opt_key)
            if opt_val:
                subprocess_env[env_key] = str(opt_val)
        try:
            # Allow SIGINT to pass to psql to abort queries.
            signal.signal(signal.SIGINT, signal.SIG_IGN)
            subprocess.run(args, check=True, env=subprocess_env)
        finally:
            # Restore the original SIGINT handler.
            signal.signal(signal.SIGINT, sigint_handler)

    def runshell(self):
        DatabaseClient.runshell_db(self.connection.get_connection_params())
