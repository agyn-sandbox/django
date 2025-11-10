import unittest
from types import SimpleNamespace

from django.test import SimpleTestCase, override_settings

from django.db.backends.mysql.operations import DatabaseOperations as MySQLOperations
from django.core.exceptions import ImproperlyConfigured

try:
    from django.db.backends.oracle.operations import DatabaseOperations as OracleOperations
except ImproperlyConfigured:  # cx_Oracle isn't available.
    OracleOperations = None


class DatabaseOperationsTimezoneTests(SimpleTestCase):

    @override_settings(USE_TZ=True)
    def test_mysql_conversion_skipped_when_timezones_match(self):
        connection = SimpleNamespace(timezone_name='Europe/Paris')
        ops = MySQLOperations(connection)
        self.assertEqual(ops._convert_field_to_tz('myfield', 'Europe/Paris'), 'myfield')
        self.assertEqual(
            ops.datetime_cast_date_sql('myfield', 'Europe/Paris'),
            'DATE(myfield)'
        )
        self.assertEqual(
            ops.datetime_extract_sql('day', 'myfield', 'Europe/Paris'),
            'EXTRACT(DAY FROM myfield)'
        )

    @override_settings(USE_TZ=True)
    def test_mysql_conversion_uses_database_timezone(self):
        connection = SimpleNamespace(timezone_name='Europe/Paris')
        ops = MySQLOperations(connection)
        self.assertEqual(
            ops._convert_field_to_tz('myfield', 'UTC'),
            "CONVERT_TZ(myfield, 'Europe/Paris', 'UTC')"
        )
        self.assertEqual(
            ops.datetime_cast_date_sql('myfield', 'UTC'),
            "DATE(CONVERT_TZ(myfield, 'Europe/Paris', 'UTC'))"
        )
        trunc_sql = ops.datetime_trunc_sql('day', 'myfield', 'UTC')
        self.assertIn("CONVERT_TZ(myfield, 'Europe/Paris', 'UTC')", trunc_sql)

    @override_settings(USE_TZ=True)
    @unittest.skipUnless(OracleOperations, 'Oracle backend not available')
    def test_oracle_conversion_skipped_when_timezones_match(self):
        connection = SimpleNamespace(timezone_name='Europe/Paris')
        ops = OracleOperations(connection)
        self.assertEqual(ops._convert_field_to_tz('myfield', 'Europe/Paris'), 'myfield')
        self.assertEqual(
            ops.datetime_extract_sql('day', 'myfield', 'Europe/Paris'),
            "EXTRACT(DAY FROM myfield)"
        )

    @override_settings(USE_TZ=True)
    @unittest.skipUnless(OracleOperations, 'Oracle backend not available')
    def test_oracle_conversion_uses_database_timezone(self):
        connection = SimpleNamespace(timezone_name='Europe/Paris')
        ops = OracleOperations(connection)
        converted = ops._convert_field_to_tz('myfield', 'UTC')
        self.assertEqual(
            converted,
            "CAST((FROM_TZ(myfield, 'Europe/Paris') AT TIME ZONE 'UTC') AS TIMESTAMP)"
        )
        trunc_sql = ops.datetime_trunc_sql('day', 'myfield', 'UTC')
        self.assertIn("FROM_TZ(myfield, 'Europe/Paris') AT TIME ZONE 'UTC'", trunc_sql)
