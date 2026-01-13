import datetime
from unittest import mock

from django.db import connection
from django.test import TestCase, skipUnlessDBFeature
from django.test.utils import CaptureQueriesContext

from .models import (
    DumbCategory,
    NonIntegerPKReturningModel,
    ReturningModel,
    WrappedAutoFieldModel,
    WrappedInt,
)


@skipUnlessDBFeature("can_return_columns_from_insert")
class ReturningValuesTests(TestCase):
    def test_insert_returning(self):
        with CaptureQueriesContext(connection) as captured_queries:
            DumbCategory.objects.create()
        self.assertIn(
            "RETURNING %s.%s"
            % (
                connection.ops.quote_name(DumbCategory._meta.db_table),
                connection.ops.quote_name(DumbCategory._meta.get_field("id").column),
            ),
            captured_queries[-1]["sql"],
        )

    def test_insert_returning_non_integer(self):
        obj = NonIntegerPKReturningModel.objects.create()
        self.assertTrue(obj.created)
        self.assertIsInstance(obj.created, datetime.datetime)

    def test_insert_returning_non_integer_from_literal_value(self):
        obj = NonIntegerPKReturningModel.objects.create(pk="2025-01-01")
        self.assertTrue(obj.created)
        self.assertIsInstance(obj.created, datetime.datetime)

    def test_insert_returning_multiple(self):
        with CaptureQueriesContext(connection) as captured_queries:
            obj = ReturningModel.objects.create()
        table_name = connection.ops.quote_name(ReturningModel._meta.db_table)
        self.assertIn(
            "RETURNING %s.%s, %s.%s"
            % (
                table_name,
                connection.ops.quote_name(ReturningModel._meta.get_field("id").column),
                table_name,
                connection.ops.quote_name(
                    ReturningModel._meta.get_field("created").column
                ),
            ),
            captured_queries[-1]["sql"],
        )
        self.assertEqual(
            captured_queries[-1]["sql"]
            .split("RETURNING ")[1]
            .count(
                connection.ops.quote_name(
                    ReturningModel._meta.get_field("created").column
                ),
            ),
            1,
        )
        self.assertTrue(obj.pk)
        self.assertIsInstance(obj.created, datetime.datetime)

    @skipUnlessDBFeature("can_return_rows_from_bulk_insert")
    def test_bulk_insert(self):
        objs = [ReturningModel(), ReturningModel(pk=2**11), ReturningModel()]
        ReturningModel.objects.bulk_create(objs)
        for obj in objs:
            with self.subTest(obj=obj):
                self.assertTrue(obj.pk)
                self.assertIsInstance(obj.created, datetime.datetime)


class ReturningValueConvertersTests(TestCase):
    def test_insert_returning_runs_pk_converters(self):
        with (
            mock.patch.object(
                type(connection.features),
                "can_return_columns_from_insert",
                True,
            ),
            mock.patch(
                "django.db.models.query.QuerySet._insert",
                return_value=[(1,)],
            ),
        ):
            obj = WrappedAutoFieldModel()
            obj.save()
        self.assertIsInstance(obj.pk, WrappedInt)

    def test_bulk_insert_runs_pk_converters(self):
        objs = [WrappedAutoFieldModel(), WrappedAutoFieldModel()]
        with (
            mock.patch.object(
                type(connection.features),
                "can_return_rows_from_bulk_insert",
                True,
            ),
            mock.patch(
                "django.db.models.query.QuerySet._insert",
                return_value=[(1,), (2,)],
            ),
        ):
            WrappedAutoFieldModel.objects.bulk_create(objs)
        for obj in objs:
            with self.subTest(obj=obj):
                self.assertIsInstance(obj.pk, WrappedInt)

    @skipUnlessDBFeature('supports_ignore_conflicts')
    def test_bulk_insert_ignore_conflicts_without_returning(self):
        objs = WrappedAutoFieldModel.objects.bulk_create([
            WrappedAutoFieldModel(),
            WrappedAutoFieldModel(),
        ], ignore_conflicts=True)
        self.assertEqual(WrappedAutoFieldModel.objects.count(), 2)
        for obj in objs:
            with self.subTest(obj=obj):
                self.assertIsNone(obj.pk)
