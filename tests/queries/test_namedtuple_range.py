from collections import namedtuple

from django.test import TestCase

from .models import Number


class NamedTupleRangeLookupTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Number.objects.bulk_create([
            Number(num=v) for v in [1, 2, 3, 4, 5]
        ])

    def test_range_with_namedtuple_matches_tuple(self):
        Range = namedtuple('Range', ['start', 'end'])
        nt = Range(2, 4)
        # Namedtuple should not raise and should match tuple behavior.
        qs_named = Number.objects.filter(num__range=nt).order_by('id')
        qs_tuple = Number.objects.filter(num__range=(2, 4)).order_by('id')
        self.assertEqual(list(qs_named.values_list('id', flat=True)), list(qs_tuple.values_list('id', flat=True)))

    def test_range_with_namedtuple_no_typeerror(self):
        Range = namedtuple('Range', ['start', 'end'])
        nt = Range(1, 3)
        # Assert no exception is thrown by filter evaluation.
        list(Number.objects.filter(num__range=nt))
