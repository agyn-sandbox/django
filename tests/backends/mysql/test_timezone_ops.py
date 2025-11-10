from django.db.backends.mysql.operations import DatabaseOperations
from django.test import SimpleTestCase, override_settings
from django.utils import timezone


class FakeConnection:
    def __init__(self, tzname):
        self.timezone_name = tzname


class TimezoneConversionSQLTests(SimpleTestCase):
    def setUp(self):
        self.addCleanup(timezone.deactivate)

    @override_settings(USE_TZ=True, TIME_ZONE='Europe/Paris')
    def test_date_cast_elides_convert_when_same_tz(self):
        timezone.activate('Europe/Paris')
        ops = DatabaseOperations(FakeConnection('Europe/Paris'))
        tzname = timezone.get_current_timezone_name()
        sql = ops.datetime_cast_date_sql('my_field', tzname)
        self.assertEqual(sql, "DATE(my_field)")

    @override_settings(USE_TZ=True, TIME_ZONE='Europe/Paris')
    def test_date_cast_converts_from_db_tz(self):
        timezone.activate('Europe/Paris')
        ops = DatabaseOperations(FakeConnection('America/New_York'))
        tzname = timezone.get_current_timezone_name()
        sql = ops.datetime_cast_date_sql('my_field', tzname)
        self.assertEqual(
            sql,
            "DATE(CONVERT_TZ(my_field, 'America/New_York', 'Europe/Paris'))",
        )

    @override_settings(USE_TZ=True, TIME_ZONE='Europe/Paris')
    def test_date_cast_defaults_from_utc_when_db_tz_unset(self):
        timezone.activate('Europe/Paris')
        ops = DatabaseOperations(FakeConnection(None))
        tzname = timezone.get_current_timezone_name()
        sql = ops.datetime_cast_date_sql('my_field', tzname)
        self.assertEqual(
            sql,
            "DATE(CONVERT_TZ(my_field, 'UTC', 'Europe/Paris'))",
        )

    @override_settings(USE_TZ=True, TIME_ZONE='Europe/Paris')
    def test_datetime_extract_uses_db_timezone(self):
        timezone.activate('Europe/Paris')
        ops = DatabaseOperations(FakeConnection('America/New_York'))
        tzname = timezone.get_current_timezone_name()
        sql = ops.datetime_extract_sql('year', 'my_field', tzname)
        self.assertEqual(
            sql,
            "EXTRACT(YEAR FROM CONVERT_TZ(my_field, 'America/New_York', 'Europe/Paris'))",
        )
