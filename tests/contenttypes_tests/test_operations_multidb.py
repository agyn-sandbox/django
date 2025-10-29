from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.test import TransactionTestCase, override_settings


class ContentTypesRouter:
    """
    Route django.contrib.contenttypes reads/writes/migrations to 'other'.
    Disallow contenttypes migrations on 'default'.
    """

    app_label = 'contenttypes'

    def db_for_read(self, model, **hints):
        if model._meta.app_label == self.app_label:
            return 'other'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == self.app_label:
            # Intentionally route writes to 'default' to simulate
            # pre-fix behavior. The fix under test forces using the
            # schema editor's alias ('other') for the save.
            return 'default'
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == self.app_label:
            return db == 'other'
        return None


@override_settings(
    MIGRATION_MODULES=dict(
        # Reuse the operations migrations used by existing contenttypes tests.
        settings.MIGRATION_MODULES,
        contenttypes_tests='contenttypes_tests.operations_migrations',
    ),
    DATABASE_ROUTERS=[
        'contenttypes_tests.test_operations_multidb.ContentTypesRouter',
    ],
)
class ContentTypeOperationsMultiDBTests(TransactionTestCase):
    available_apps = [
        'contenttypes_tests',
        'django.contrib.contenttypes',
    ]
    databases = {'default', 'other'}

    def test_rename_model_saves_contenttype_on_schema_editor_alias(self):
        # Seed ContentType on 'other'.
        ContentType.objects.using('other').create(
            app_label='contenttypes_tests',
            model='foo',
        )

        # Apply migrations for contenttypes_tests which includes RenameModel.
        call_command(
            'migrate',
            'contenttypes_tests',
            database='other',
            interactive=False,
            verbosity=0,
        )

        # Assert rename occurred on 'other' and 'default' untouched.
        self.assertTrue(
            ContentType.objects.using('other').filter(
                app_label='contenttypes_tests',
                model='renamedfoo',
            ).exists()
        )
        self.assertFalse(
            ContentType.objects.using('other').filter(
                app_label='contenttypes_tests',
                model='foo',
            ).exists()
        )

        # Default should not be touched by the rename: neither 'foo' nor
        # 'renamedfoo' should exist.
        self.assertFalse(
            ContentType.objects.using('default').filter(
                app_label='contenttypes_tests',
                model='foo',
            ).exists()
        )
        self.assertFalse(
            ContentType.objects.using('default').filter(
                app_label='contenttypes_tests',
                model='renamedfoo',
            ).exists()
        )
