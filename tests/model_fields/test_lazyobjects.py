import uuid

from django.test import TestCase
from django.utils.functional import SimpleLazyObject

from .models import BigS, IntegerModel, UUIDModel


class SimpleLazyObjectFilterTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.char_obj = BigS.objects.create(s='lazy-slug')
        cls.int_obj = IntegerModel.objects.create(value=42)
        cls.uuid_value = uuid.uuid4()
        cls.uuid_obj = UUIDModel.objects.create(field=cls.uuid_value)

    def test_char_field_filter_with_lazy_object(self):
        lazy_value = SimpleLazyObject(lambda: self.char_obj.s)
        self.assertEqual(list(BigS.objects.filter(s=lazy_value)), [self.char_obj])

    def test_integer_field_filter_with_lazy_object(self):
        lazy_value = SimpleLazyObject(lambda: self.int_obj.value)
        self.assertEqual(list(IntegerModel.objects.filter(value=lazy_value)), [self.int_obj])

    def test_uuid_field_filter_with_lazy_object(self):
        lazy_value = SimpleLazyObject(lambda: self.uuid_value)
        self.assertEqual(list(UUIDModel.objects.filter(field=lazy_value)), [self.uuid_obj])
