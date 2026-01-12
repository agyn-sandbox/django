import importlib
import sys
import types
from types import SimpleNamespace
from unittest import mock

from django.test import SimpleTestCase, override_settings

fake_base = types.ModuleType('django.db.backends.oracle.base')
fake_base.Database = SimpleNamespace(
    LOB=type('FakeLOB', (), {}),
    Timestamp=type('FakeTimestamp', (), {}),
    TIMESTAMP=object(),
)
sys.modules.setdefault('django.db.backends.oracle.base', fake_base)
sys.modules.setdefault('cx_Oracle', mock.MagicMock())
DatabaseOperations = importlib.import_module('django.db.backends.oracle.operations').DatabaseOperations


class TimezoneConversionSQLTests(SimpleTestCase):
    field_name = 'created_at'

    def _get_ops(self, db_timezone):
        connection = SimpleNamespace(timezone_name=db_timezone)
        return DatabaseOperations(connection=connection)

    def _collect_sql(self, ops, tzname):
        return [
            ops.datetime_cast_date_sql(self.field_name, tzname),
            ops.datetime_cast_time_sql(self.field_name, tzname),
            ops.datetime_extract_sql('day', self.field_name, tzname),
            ops.datetime_trunc_sql('day', self.field_name, tzname),
        ]

    @override_settings(USE_TZ=False)
    def test_use_tz_disabled(self):
        ops = self._get_ops('UTC')
        sql_fragments = self._collect_sql(ops, 'Europe/Paris')
        for sql in sql_fragments:
            self.assertNotIn('FROM_TZ', sql)

    @override_settings(USE_TZ=True)
    def test_same_timezone_no_conversion(self):
        ops = self._get_ops('UTC')
        sql_fragments = self._collect_sql(ops, 'UTC')
        for sql in sql_fragments:
            self.assertNotIn('FROM_TZ', sql)

    @override_settings(USE_TZ=True)
    def test_utc_to_paris_conversion(self):
        ops = self._get_ops('UTC')
        sql_fragments = self._collect_sql(ops, 'Europe/Paris')
        expected_substring = "FROM_TZ(%s, 'UTC') AT TIME ZONE 'Europe/Paris'" % self.field_name
        for sql in sql_fragments:
            self.assertIn(expected_substring, sql)

    @override_settings(USE_TZ=True)
    def test_paris_to_utc_conversion(self):
        ops = self._get_ops('Europe/Paris')
        sql_fragments = self._collect_sql(ops, 'UTC')
        expected_substring = "FROM_TZ(%s, 'Europe/Paris') AT TIME ZONE 'UTC'" % self.field_name
        for sql in sql_fragments:
            self.assertIn(expected_substring, sql)
