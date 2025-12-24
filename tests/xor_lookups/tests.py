from django.db.models import Q
from django.test import TestCase

from .models import Number


class XorLookupsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.numbers = [Number.objects.create(num=i) for i in range(10)]

    def test_filter(self):
        self.assertCountEqual(
            Number.objects.filter(num__lte=7) ^ Number.objects.filter(num__gte=3),
            self.numbers[:3] + self.numbers[8:],
        )
        self.assertCountEqual(
            Number.objects.filter(Q(num__lte=7) ^ Q(num__gte=3)),
            self.numbers[:3] + self.numbers[8:],
        )

    def test_filter_negated(self):
        self.assertCountEqual(
            Number.objects.filter(Q(num__lte=7) ^ ~Q(num__lt=3)),
            self.numbers[:3] + self.numbers[8:],
        )
        self.assertCountEqual(
            Number.objects.filter(~Q(num__gt=7) ^ ~Q(num__lt=3)),
            self.numbers[:3] + self.numbers[8:],
        )
        self.assertCountEqual(
            Number.objects.filter(Q(num__lte=7) ^ ~Q(num__lt=3) ^ Q(num__lte=1)),
            [self.numbers[2]] + self.numbers[8:],
        )
        self.assertCountEqual(
            Number.objects.filter(~(Q(num__lte=7) ^ ~Q(num__lt=3) ^ Q(num__lte=1))),
            self.numbers[:2] + self.numbers[3:8],
        )

    def test_exclude(self):
        self.assertCountEqual(
            Number.objects.exclude(Q(num__lte=7) ^ Q(num__gte=3)),
            self.numbers[3:8],
        )

    def test_stages(self):
        numbers = Number.objects.all()
        self.assertSequenceEqual(
            numbers.filter(num__gte=0) ^ numbers.filter(num__lte=11),
            [],
        )
        self.assertSequenceEqual(
            numbers.filter(num__gt=0) ^ numbers.filter(num__lt=11),
            [self.numbers[0]],
        )

    def test_pk_q(self):
        self.assertCountEqual(
            Number.objects.filter(Q(pk=self.numbers[0].pk) ^ Q(pk=self.numbers[1].pk)),
            self.numbers[:2],
        )

    def test_empty_in(self):
        self.assertCountEqual(
            Number.objects.filter(Q(pk__in=[]) ^ Q(num__gte=5)),
            self.numbers[5:],
        )

    def test_xor_parity_multiple_arguments_with_duplicates(self):
        # On backends without native XOR, ensure parity (odd number of truths)
        # semantics for chained XOR with duplicate conditions.
        target = self.numbers[3]
        q = Q(pk=target.pk)
        self.assertCountEqual(Number.objects.filter(q), [target])
        self.assertCountEqual(Number.objects.filter(q ^ q), [])
        self.assertCountEqual(Number.objects.filter(q ^ q ^ q), [target])
        self.assertCountEqual(Number.objects.filter(q ^ q ^ q ^ q), [])
        self.assertCountEqual(Number.objects.filter(q ^ q ^ q ^ q ^ q), [target])
