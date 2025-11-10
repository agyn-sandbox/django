import datetime
from contextlib import contextmanager

import pytz

from django.db import connection, models
from django.db.models.functions import ExtractHour, TruncDay, TruncHour
from django.test import TransactionTestCase, override_settings
from django.utils import timezone


@contextmanager
def database_timezone(db_connection, tzname):
    original = db_connection.settings_dict.get('TIME_ZONE')
    db_connection.close()
    db_connection.settings_dict['TIME_ZONE'] = tzname
    for attr in ('timezone', 'timezone_name'):
        db_connection.__dict__.pop(attr, None)
    try:
        db_connection.ensure_connection()
        yield
    finally:
        db_connection.close()
        db_connection.settings_dict['TIME_ZONE'] = original
        for attr in ('timezone', 'timezone_name'):
            db_connection.__dict__.pop(attr, None)


class SQLiteDatabaseTimezoneTests(TransactionTestCase):
    databases = {'default'}
    available_apps = []

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if connection.vendor != 'sqlite':
            raise cls.skipTest('SQLite tests')

        class TimezoneRecord(models.Model):
            name = models.CharField(max_length=32)
            start_datetime = models.DateTimeField()

            class Meta:
                app_label = 'sqlite_timezone_tests'
                db_table = 'tz_timezone_tests_model'

        cls.model = TimezoneRecord
        with connection.schema_editor() as editor:
            editor.create_model(cls.model)

    @classmethod
    def tearDownClass(cls):
        if connection.vendor == 'sqlite' and hasattr(cls, 'model'):
            with connection.schema_editor() as editor:
                editor.delete_model(cls.model)
        super().tearDownClass()

    def tearDown(self):
        self.model.objects.all().delete()
        super().tearDown()

    @override_settings(USE_TZ=True, TIME_ZONE='Europe/Paris')
    def test_date_lookup_without_conversion_when_timezones_match(self):
        paris = pytz.timezone('Europe/Paris')
        aware = paris.localize(datetime.datetime(2017, 7, 6, 20, 50))
        with database_timezone(connection, 'Europe/Paris'), timezone.override('Europe/Paris'):
            self.model.objects.create(name='match', start_datetime=aware)
            qs = self.model.objects.filter(start_datetime__date=datetime.date(2017, 7, 6))
            sql = str(qs.query)
            self.assertNotIn('UTC', sql)
            self.assertEqual(list(qs.values_list('name', flat=True)), ['match'])

    @override_settings(USE_TZ=True, TIME_ZONE='UTC')
    def test_date_lookup_converts_from_database_timezone(self):
        paris = pytz.timezone('Europe/Paris')
        aware = paris.localize(datetime.datetime(2017, 7, 7, 0, 30))
        with database_timezone(connection, 'Europe/Paris'), timezone.override('UTC'):
            self.model.objects.create(name='offset', start_datetime=aware)
            lookup_date = datetime.date(2017, 7, 6)
            qs = self.model.objects.filter(start_datetime__date=lookup_date)
            self.assertIn("'Europe/Paris'", str(qs.query))
            self.assertEqual(list(qs.values_list('name', flat=True)), ['offset'])
            hour = (
                self.model.objects
                .annotate(hour=ExtractHour('start_datetime'))
                .values_list('hour', flat=True)
                .get()
            )
            self.assertEqual(hour, 22)
            truncated = (
                self.model.objects
                .annotate(day=TruncDay('start_datetime'))
                .values_list('day', flat=True)
                .get()
            )
            self.assertEqual(truncated, datetime.datetime(2017, 7, 6, 0, 0, tzinfo=timezone.utc))

    @override_settings(USE_TZ=True, TIME_ZONE='UTC')
    def test_dst_boundary_near_midnight(self):
        new_york = pytz.timezone('America/New_York')
        aware = new_york.localize(datetime.datetime(2019, 11, 3, 1, 30), is_dst=False)
        with database_timezone(connection, 'America/New_York'), timezone.override('UTC'):
            self.model.objects.create(name='dst', start_datetime=aware)
            lookup_date = datetime.date(2019, 11, 3)
            qs = self.model.objects.filter(start_datetime__date=lookup_date)
            self.assertEqual(list(qs.values_list('name', flat=True)), ['dst'])
            extracted_hour = (
                self.model.objects
                .annotate(hour=ExtractHour('start_datetime'))
                .values_list('hour', flat=True)
                .get()
            )
            self.assertEqual(extracted_hour, 6)
            truncated_hour = (
                self.model.objects
                .annotate(hour_start=TruncHour('start_datetime'))
                .values_list('hour_start', flat=True)
                .get()
            )
            self.assertEqual(truncated_hour, datetime.datetime(2019, 11, 3, 6, 0, tzinfo=timezone.utc))
