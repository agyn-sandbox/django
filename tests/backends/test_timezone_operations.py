from zoneinfo import ZoneInfo

import pytz

from django.db.backends.mysql.operations import (
    DatabaseOperations as MySQLDatabaseOperations,
)
from django.db.backends.postgresql.operations import (
    DatabaseOperations as PostgresDatabaseOperations,
)
from django.db.models import DateTimeField
from django.db.models.expressions import RawSQL
from django.db.models.functions import ExtractHour, TruncDay
from django.test import SimpleTestCase, override_settings


class _BaseFakeConnection:
    timezone_name = 'UTC'

    def __init__(self):
        self.ops = None


class _FakePostgresConnection(_BaseFakeConnection):
    vendor = 'postgresql'

    def __init__(self):
        super().__init__()
        self.ops = PostgresDatabaseOperations(self)


class _FakeMySQLConnection(_BaseFakeConnection):
    vendor = 'mysql'

    def __init__(self):
        super().__init__()
        self.ops = MySQLDatabaseOperations(self)


class _FakeCompiler:
    def __init__(self, connection):
        self.connection = connection

    def compile(self, node):
        return node.as_sql(self, self.connection)

    def quote_name_unless_alias(self, value):
        return value


def _datetime_column_expression():
    field = DateTimeField()
    field.set_attributes_from_name('last_updated')
    return RawSQL('"backends_schoolclass"."last_updated"', [], output_field=field)


class PostgreSQLPrepareTznameDeltaTests(SimpleTestCase):
    def setUp(self):
        self.ops = _FakePostgresConnection().ops

    def test_preserves_etc_gmt_zone(self):
        self.assertEqual(self.ops._prepare_tzname_delta('Etc/GMT-10'), 'Etc/GMT-10')

    def test_flip_numeric_offsets(self):
        self.assertEqual(self.ops._prepare_tzname_delta('+10'), '-10')
        self.assertEqual(self.ops._prepare_tzname_delta('-05:30'), '+05:30')
        self.assertEqual(self.ops._prepare_tzname_delta('+1000'), '-1000')

    def test_preserves_named_zone(self):
        self.assertEqual(self.ops._prepare_tzname_delta('Europe/London'), 'Europe/London')


class MySQLPrepareTznameDeltaTests(SimpleTestCase):
    def setUp(self):
        self.ops = _FakeMySQLConnection().ops

    def test_translates_etc_gmt_zone(self):
        self.assertEqual(self.ops._prepare_tzname_delta('Etc/GMT-10'), '+10:00')

    def test_normalizes_numeric_offsets(self):
        self.assertEqual(self.ops._prepare_tzname_delta('+10'), '+10:00')
        self.assertEqual(self.ops._prepare_tzname_delta('-05:30'), '-05:30')
        self.assertEqual(self.ops._prepare_tzname_delta('+1000'), '+10:00')

    def test_preserves_named_zone(self):
        self.assertEqual(self.ops._prepare_tzname_delta('America/New_York'), 'America/New_York')


@override_settings(USE_TZ=True)
class BackendTimezoneSQLCompilationTests(SimpleTestCase):
    def setUp(self):
        self.postgres_connection = _FakePostgresConnection()
        self.mysql_connection = _FakeMySQLConnection()

    def _compile(self, connection, expression):
        compiler = _FakeCompiler(connection)
        sql, params = expression.as_sql(compiler, connection)
        return sql, params

    def _assert_params_empty(self, params):
        self.assertEqual(params, [])

    def test_postgres_truncday_with_pytz_timezone(self):
        expression = TruncDay(_datetime_column_expression(), tzinfo=pytz.timezone('Etc/GMT-10'))
        sql, params = self._compile(self.postgres_connection, expression)
        self._assert_params_empty(params)
        self.assertIn("AT TIME ZONE 'Etc/GMT-10'", sql)

    def test_postgres_truncday_with_zoneinfo_timezone(self):
        expression = TruncDay(_datetime_column_expression(), tzinfo=ZoneInfo('Etc/GMT-10'))
        sql, params = self._compile(self.postgres_connection, expression)
        self._assert_params_empty(params)
        self.assertIn("AT TIME ZONE 'Etc/GMT-10'", sql)

    def test_mysql_extracthour_with_pytz_timezone(self):
        expression = ExtractHour(_datetime_column_expression(), tzinfo=pytz.timezone('Etc/GMT-10'))
        sql, params = self._compile(self.mysql_connection, expression)
        self._assert_params_empty(params)
        self.assertIn('CONVERT_TZ', sql)
        self.assertIn("'+10:00'", sql)

    def test_mysql_extracthour_with_zoneinfo_timezone(self):
        expression = ExtractHour(_datetime_column_expression(), tzinfo=ZoneInfo('Etc/GMT-10'))
        sql, params = self._compile(self.mysql_connection, expression)
        self._assert_params_empty(params)
        self.assertIn('CONVERT_TZ', sql)
        self.assertIn("'+10:00'", sql)
