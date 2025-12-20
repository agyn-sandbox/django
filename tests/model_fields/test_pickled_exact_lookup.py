from django.test import TestCase

from .models import PickledTypePreservingModel


class PickledIterableExactLookupTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.model = PickledTypePreservingModel
        cls.list_value = ["alpha", "beta"]
        cls.tuple_value = ("alpha", "beta")
        cls.list_instance = cls.model.objects.create(payload=cls.list_value)
        cls.tuple_instance = cls.model.objects.create(payload=cls.tuple_value)
        cls.list_instance.refresh_from_db()
        cls.tuple_instance.refresh_from_db()

    def test_exact_lookup_preserves_iterable_type(self):
        self.assertEqual(
            self.model.objects.get(payload__exact=self.list_value),
            self.list_instance,
        )
        self.assertEqual(
            self.model.objects.get(payload__exact=self.tuple_value),
            self.tuple_instance,
        )

    def test_iexact_lookup_preserves_iterable_type(self):
        self.assertEqual(
            self.model.objects.get(payload__iexact=self.list_value),
            self.list_instance,
        )
        self.assertEqual(
            self.model.objects.get(payload__iexact=self.tuple_value),
            self.tuple_instance,
        )

    def test_implicit_exact_lookup_preserves_iterable_type(self):
        self.assertEqual(
            self.model.objects.get(payload=self.list_value),
            self.list_instance,
        )
        self.assertEqual(
            self.model.objects.get(payload=self.tuple_value),
            self.tuple_instance,
        )
