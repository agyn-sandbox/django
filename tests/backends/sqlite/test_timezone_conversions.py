from types import SimpleNamespace

from django.db.backends.sqlite3.base import (
    _sqlite_datetime_cast_time,
)
from django.db.backends.sqlite3.operations import DatabaseOperations
from django.test import SimpleTestCase, override_settings


class SQLiteTimezoneConversionFunctionTests(SimpleTestCase):
    sample_datetime = '2025-01-15 12:30:00'

    @override_settings(USE_TZ=False)
    def test_use_tz_disabled(self):
        self.assertEqual(
            _sqlite_datetime_cast_time(self.sample_datetime, None, None),
            '12:30:00',
        )

    @override_settings(USE_TZ=True)
    def test_same_timezone_no_conversion(self):
        self.assertEqual(
            _sqlite_datetime_cast_time(self.sample_datetime, 'UTC', 'UTC'),
            '12:30:00',
        )

    @override_settings(USE_TZ=True)
    def test_utc_to_paris_conversion(self):
        self.assertEqual(
            _sqlite_datetime_cast_time(self.sample_datetime, 'UTC', 'Europe/Paris'),
            '13:30:00',
        )

    @override_settings(USE_TZ=True)
    def test_paris_to_utc_conversion(self):
        self.assertEqual(
            _sqlite_datetime_cast_time(self.sample_datetime, 'Europe/Paris', 'UTC'),
            '11:30:00',
        )


class SQLiteTimezoneConversionSQLTests(SimpleTestCase):
    field_name = 'created_at'

    def _ops(self, db_timezone):
        connection = SimpleNamespace(timezone_name=db_timezone)
        return DatabaseOperations(connection=connection)

    @override_settings(USE_TZ=False)
    def test_use_tz_disabled(self):
        ops = self._ops('UTC')
        self.assertEqual(
            ops.datetime_cast_time_sql(self.field_name, 'Europe/Paris'),
            "django_datetime_cast_time(%s, NULL, NULL)" % self.field_name,
        )

    @override_settings(USE_TZ=True)
    def test_same_timezone_no_conversion(self):
        ops = self._ops('UTC')
        self.assertEqual(
            ops.datetime_cast_time_sql(self.field_name, 'UTC'),
            "django_datetime_cast_time(%s, 'UTC', 'UTC')" % self.field_name,
        )

    @override_settings(USE_TZ=True)
    def test_paris_to_utc_conversion(self):
        ops = self._ops('Europe/Paris')
        self.assertEqual(
            ops.datetime_cast_time_sql(self.field_name, 'UTC'),
            "django_datetime_cast_time(%s, 'Europe/Paris', 'UTC')" % self.field_name,
        )
