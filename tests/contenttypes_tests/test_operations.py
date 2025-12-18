from django.apps.registry import apps
from django.conf import settings
from django.contrib.contenttypes import management as contenttypes_management
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.db import migrations, models
from django.test import TransactionTestCase, override_settings


class WriteToDefaultRouter:
    def db_for_read(self, model, **hints):
        return 'other'

    def db_for_write(self, model, **hints):
        return 'default'


@override_settings(
    MIGRATION_MODULES=dict(
        settings.MIGRATION_MODULES,
        contenttypes_tests='contenttypes_tests.operations_migrations',
    ),
)
class ContentTypeOperationsTests(TransactionTestCase):
    available_apps = [
        'contenttypes_tests',
        'django.contrib.contenttypes',
    ]

    def setUp(self):
        app_config = apps.get_app_config('contenttypes_tests')
        models.signals.post_migrate.connect(self.assertOperationsInjected, sender=app_config)

    def tearDown(self):
        app_config = apps.get_app_config('contenttypes_tests')
        models.signals.post_migrate.disconnect(self.assertOperationsInjected, sender=app_config)

    def assertOperationsInjected(self, plan, **kwargs):
        for migration, _backward in plan:
            operations = iter(migration.operations)
            for operation in operations:
                if isinstance(operation, migrations.RenameModel):
                    next_operation = next(operations)
                    self.assertIsInstance(next_operation, contenttypes_management.RenameContentType)
                    self.assertEqual(next_operation.app_label, migration.app_label)
                    self.assertEqual(next_operation.old_model, operation.old_name_lower)
                    self.assertEqual(next_operation.new_model, operation.new_name_lower)

    def test_existing_content_type_rename(self):
        ContentType.objects.create(app_label='contenttypes_tests', model='foo')
        call_command('migrate', 'contenttypes_tests', database='default', interactive=False, verbosity=0,)
        self.assertFalse(ContentType.objects.filter(app_label='contenttypes_tests', model='foo').exists())
        self.assertTrue(ContentType.objects.filter(app_label='contenttypes_tests', model='renamedfoo').exists())
        call_command('migrate', 'contenttypes_tests', 'zero', database='default', interactive=False, verbosity=0)
        self.assertTrue(ContentType.objects.filter(app_label='contenttypes_tests', model='foo').exists())
        self.assertFalse(ContentType.objects.filter(app_label='contenttypes_tests', model='renamedfoo').exists())

    def test_missing_content_type_rename_ignore(self):
        call_command('migrate', 'contenttypes_tests', database='default', interactive=False, verbosity=0,)
        self.assertFalse(ContentType.objects.filter(app_label='contenttypes_tests', model='foo').exists())
        self.assertTrue(ContentType.objects.filter(app_label='contenttypes_tests', model='renamedfoo').exists())
        call_command('migrate', 'contenttypes_tests', 'zero', database='default', interactive=False, verbosity=0)
        self.assertTrue(ContentType.objects.filter(app_label='contenttypes_tests', model='foo').exists())
        self.assertFalse(ContentType.objects.filter(app_label='contenttypes_tests', model='renamedfoo').exists())

    def test_content_type_rename_conflict(self):
        ContentType.objects.create(app_label='contenttypes_tests', model='foo')
        ContentType.objects.create(app_label='contenttypes_tests', model='renamedfoo')
        call_command('migrate', 'contenttypes_tests', database='default', interactive=False, verbosity=0)
        self.assertTrue(ContentType.objects.filter(app_label='contenttypes_tests', model='foo').exists())
        self.assertTrue(ContentType.objects.filter(app_label='contenttypes_tests', model='renamedfoo').exists())
        call_command('migrate', 'contenttypes_tests', 'zero', database='default', interactive=False, verbosity=0)
        self.assertTrue(ContentType.objects.filter(app_label='contenttypes_tests', model='foo').exists())
        self.assertTrue(ContentType.objects.filter(app_label='contenttypes_tests', model='renamedfoo').exists())


@override_settings(
    MIGRATION_MODULES=dict(
        settings.MIGRATION_MODULES,
        contenttypes_tests='contenttypes_tests.operations_migrations',
    ),
    DATABASE_ROUTERS=[WriteToDefaultRouter()],
)
class ContentTypeOperationsMultidbTests(TransactionTestCase):
    available_apps = [
        'contenttypes_tests',
        'django.contrib.contenttypes',
    ]
    databases = {'default', 'other'}

    def test_rename_uses_schema_editor_database(self):
        other_manager = ContentType.objects.db_manager('other')
        other_manager.create(app_label='contenttypes_tests', model='foo')

        call_command('migrate', 'contenttypes_tests', database='other', interactive=False, verbosity=0)

        self.assertFalse(
            other_manager.filter(app_label='contenttypes_tests', model='foo').exists()
        )
        self.assertTrue(
            other_manager.filter(app_label='contenttypes_tests', model='renamedfoo').exists()
        )
        self.assertFalse(
            ContentType.objects.db_manager('default')
            .filter(app_label='contenttypes_tests', model='renamedfoo')
            .exists()
        )

        call_command('migrate', 'contenttypes_tests', 'zero', database='other', interactive=False, verbosity=0)

        self.assertTrue(
            other_manager.filter(app_label='contenttypes_tests', model='foo').exists()
        )
        self.assertFalse(
            other_manager.filter(app_label='contenttypes_tests', model='renamedfoo').exists()
        )
