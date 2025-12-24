import copy
import os
import tempfile
from io import StringIO

from django.conf import settings
from django.core.management import CommandError, call_command
from django.db import connections
from django.db.migrations.exceptions import MigrationRecorderNotAllowed
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.recorder import MigrationRecorder
from django.test import TransactionTestCase, override_settings


class RecorderDisallowRouter:
    blocked_aliases = {'other', 'router'}

    def allow_migrate(self, db, app_label, **hints):
        if db in self.blocked_aliases and app_label == 'migrations':
            return False
        return None


@override_settings(DATABASE_ROUTERS=[RecorderDisallowRouter()])
class MigrationRecorderRouterTests(TransactionTestCase):
    databases = {'default', 'other'}
    available_apps = None

    MESSAGE = "Migrations are disallowed for recorder per router."

    def setUp(self):
        super().setUp()
        self.connection = connections['other']
        self.addCleanup(self.connection.close)
        self.recorder = MigrationRecorder(self.connection)

    def test_ensure_schema_disallowed(self):
        with self.assertRaisesMessage(MigrationRecorderNotAllowed, self.MESSAGE):
            self.recorder.ensure_schema()

    def test_record_operations_disallowed(self):
        self.assertEqual(self.recorder.applied_migrations(), {})
        with self.assertRaisesMessage(MigrationRecorderNotAllowed, self.MESSAGE):
            self.recorder.record_applied('test_app', '0001_initial')
        with self.assertRaisesMessage(MigrationRecorderNotAllowed, self.MESSAGE):
            self.recorder.record_unapplied('test_app', '0001_initial')
        with self.assertRaisesMessage(MigrationRecorderNotAllowed, self.MESSAGE):
            self.recorder.flush()

    def test_executor_migrate_disallowed(self):
        executor = MigrationExecutor(self.connection)
        targets = executor.loader.graph.leaf_nodes()
        with self.assertRaisesMessage(MigrationRecorderNotAllowed, self.MESSAGE):
            executor.migrate(targets)

    def test_migrate_command_run_syncdb_warns_and_skips(self):
        out = StringIO()
        call_command(
            'migrate',
            database='other',
            run_syncdb=True,
            verbosity=1,
            stdout=out,
        )
        self.assertIn("Skipping migrations for database 'other'", out.getvalue())
        self.assertEqual(self.recorder.applied_migrations(), {})

    def test_migrate_command_without_run_syncdb_errors(self):
        with self.assertRaisesMessage(CommandError, self.MESSAGE):
            call_command('migrate', database='other', verbosity=0)

    def test_test_runner_migrate_false_skips_migrations(self):
        original_name = self.connection.settings_dict['NAME']
        original_test_settings = copy.deepcopy(self.connection.settings_dict['TEST'])
        original_db_settings = copy.deepcopy(settings.DATABASES['other'])
        original_handler_settings = copy.deepcopy(connections.databases['other'])
        with tempfile.TemporaryDirectory() as tmpdir:
            new_name = os.path.join(tmpdir, 'router.sqlite3')
            new_test_settings = copy.deepcopy(original_test_settings)
            new_test_settings.update({'NAME': new_name, 'MIGRATE': False})
            settings.DATABASES['other'] = {
                **original_db_settings,
                'NAME': new_name,
                'TEST': copy.deepcopy(new_test_settings),
            }
            connections.databases['other'] = {
                **original_handler_settings,
                'NAME': new_name,
                'TEST': copy.deepcopy(new_test_settings),
            }
            self.connection.close()
            self.connection.settings_dict['NAME'] = new_name
            self.connection.settings_dict['TEST'] = copy.deepcopy(new_test_settings)
            try:
                self.connection.creation.create_test_db(
                    verbosity=0,
                    autoclobber=True,
                    serialize=False,
                    keepdb=False,
                )
                with self.connection.cursor() as cursor:
                    tables = set(self.connection.introspection.table_names(cursor))
                self.assertNotIn('django_migrations', tables)
            finally:
                self.connection.creation.destroy_test_db(original_name, verbosity=0, keepdb=False)
                self.connection.settings_dict['NAME'] = original_name
                self.connection.settings_dict['TEST'] = original_test_settings
                settings.DATABASES['other'] = original_db_settings
                connections.databases['other'] = original_handler_settings
                self.connection.close()
