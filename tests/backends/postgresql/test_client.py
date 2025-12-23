from django.db.backends.postgresql.client import DatabaseClient
from django.test import SimpleTestCase


class PostgreSQLDatabaseClientTests(SimpleTestCase):
    def test_parameters_inserted_before_dbname(self):
        settings_dict = {
            "HOST": "localhost",
            "PORT": "5432",
            "NAME": "example",
            "USER": "alice",
            "PASSWORD": "secret",
            "OPTIONS": {},
        }
        parameters = ["-c", "SELECT 1"]

        args, env = DatabaseClient.settings_to_cmd_args_env(settings_dict, parameters)

        self.assertEqual(
            args,
            [
                "psql",
                "-U",
                "alice",
                "-h",
                "localhost",
                "-p",
                "5432",
                "-c",
                "SELECT 1",
                "example",
            ],
        )
        self.assertEqual(env, {"PGPASSWORD": "secret"})

    def test_service_connection_without_dbname(self):
        settings_dict = {
            "HOST": "localhost",
            "NAME": "",
            "USER": "alice",
            "PASSWORD": "secret",
            "OPTIONS": {"service": "primary"},
        }
        parameters = ["--set", "ON_ERROR_STOP=1"]

        args, env = DatabaseClient.settings_to_cmd_args_env(settings_dict, parameters)

        self.assertEqual(
            args,
            [
                "psql",
                "-U",
                "alice",
                "-h",
                "localhost",
                "--set",
                "ON_ERROR_STOP=1",
            ],
        )
        self.assertEqual(
            env,
            {
                "PGPASSWORD": "secret",
                "PGSERVICE": "primary",
            },
        )

    def test_unix_socket_host_kept_before_parameters(self):
        settings_dict = {
            "HOST": "/var/run/postgresql",
            "NAME": "example",
            "USER": "alice",
            "OPTIONS": {},
        }
        parameters = ["-c", "SELECT 1"]

        args, env = DatabaseClient.settings_to_cmd_args_env(settings_dict, parameters)

        self.assertEqual(
            args,
            [
                "psql",
                "-U",
                "alice",
                "-h",
                "/var/run/postgresql",
                "-c",
                "SELECT 1",
                "example",
            ],
        )
        self.assertIsNone(env)

    def test_default_dbname_appended_last(self):
        settings_dict = {
            "HOST": "localhost",
            "NAME": "",
            "USER": "alice",
            "OPTIONS": {},
        }
        parameters = ["-c", "SELECT 1"]

        args, env = DatabaseClient.settings_to_cmd_args_env(settings_dict, parameters)

        self.assertEqual(
            args,
            [
                "psql",
                "-U",
                "alice",
                "-h",
                "localhost",
                "-c",
                "SELECT 1",
                "postgres",
            ],
        )
        self.assertIsNone(env)
