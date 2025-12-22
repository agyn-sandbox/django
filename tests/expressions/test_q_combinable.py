from unittest import SkipTest

from django.apps import apps
from django.db.models import BooleanField, Exists, OuterRef, Q, Value
from django.test import TestCase


class QCombinableTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        try:
            Number = apps.get_model('queries', 'Number')
            ReservedName = apps.get_model('queries', 'ReservedName')
        except LookupError as exc:
            raise SkipTest("'queries' app is not installed") from exc
        cls.Number = Number
        cls.ReservedName = ReservedName
        Number.objects.bulk_create([
            Number(num=1),
            Number(num=2),
            Number(num=3),
            Number(num=4),
        ])
        ReservedName.objects.bulk_create([
            ReservedName(name="first", order=1),
            ReservedName(name="third", order=3),
        ])

    def assertNums(self, queryset, expected):
        self.assertEqual(
            list(queryset.order_by("num").values_list("num", flat=True)),
            expected,
        )

    def test_q_and_exists(self):
        rn_exists = Exists(
            self.ReservedName.objects.filter(order=OuterRef("num"))
        )
        queryset = self.Number.objects.filter(Q(num__lt=3) & rn_exists)
        self.assertNums(queryset, [1])

    def test_exists_and_q(self):
        rn_exists = Exists(
            self.ReservedName.objects.filter(order=OuterRef("num"))
        )
        queryset = self.Number.objects.filter(rn_exists & Q(num__lt=3))
        self.assertNums(queryset, [1])

    def test_q_or_exists(self):
        rn_exists = Exists(
            self.ReservedName.objects.filter(order=OuterRef("num"))
        )
        queryset = self.Number.objects.filter(Q(num__lt=3) | rn_exists)
        self.assertNums(queryset, [1, 2, 3])

    def test_exists_or_q(self):
        rn_exists = Exists(
            self.ReservedName.objects.filter(order=OuterRef("num"))
        )
        queryset = self.Number.objects.filter(rn_exists | Q(num__lt=3))
        self.assertNums(queryset, [1, 2, 3])

    def test_q_and_boolean_expression(self):
        bool_expr = Value(True, output_field=BooleanField())
        queryset = self.Number.objects.filter(Q(num__lt=3) & bool_expr)
        self.assertNums(queryset, [1, 2])

    def test_boolean_expression_and_q(self):
        bool_expr = Value(True, output_field=BooleanField())
        queryset = self.Number.objects.filter(bool_expr & Q(num__lt=3))
        self.assertNums(queryset, [1, 2])

    def test_q_or_boolean_expression(self):
        bool_expr = Value(True, output_field=BooleanField())
        queryset = self.Number.objects.filter(Q(num__lt=3) | bool_expr)
        self.assertNums(queryset, [1, 2, 3, 4])

    def test_boolean_expression_or_q(self):
        bool_expr = Value(True, output_field=BooleanField())
        queryset = self.Number.objects.filter(bool_expr | Q(num__lt=3))
        self.assertNums(queryset, [1, 2, 3, 4])
