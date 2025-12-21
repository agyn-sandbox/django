import unittest
from sqlite3 import dbapi2
from unittest import mock

from django.core import checks
from django.db import connection
from django.test import SimpleTestCase


@unittest.skipUnless(connection.vendor == 'sqlite', 'SQLite tests')
class ValidationTests(SimpleTestCase):
    def test_sqlite_version_too_old(self):
        with mock.patch.object(dbapi2, 'sqlite_version_info', (3, 8, 2)), \
                mock.patch.object(dbapi2, 'sqlite_version', '3.8.2'):
            self.assertEqual(
                connection.validation.check(),
                [
                    checks.Error(
                        'SQLite 3.9.0 or later is required (found 3.8.2).',
                        hint=(
                            'Upgrade SQLite to ≥ 3.9.0 or switch to a supported '
                            'database backend.'
                        ),
                        id='sqlite.E001',
                    )
                ],
            )

    def test_sqlite_version_supported(self):
        with mock.patch.object(dbapi2, 'sqlite_version_info', (3, 9, 0)), \
                mock.patch.object(dbapi2, 'sqlite_version', '3.9.0'):
            self.assertEqual(connection.validation.check(), [])
