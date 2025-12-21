import pickle

from django.test import TestCase

from .models import NamedCategory


class PickledValuesQueryTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        NamedCategory.objects.create(name='alpha')
        NamedCategory.objects.create(name='bravo')

    def _clone_via_pickle(self, queryset):
        clone = NamedCategory.objects.all()
        clone.query = pickle.loads(pickle.dumps(queryset.query))
        return clone

    def test_values_preserves_dict_rows(self):
        queryset = NamedCategory.objects.order_by('id').values('id', 'name')
        expected = list(queryset)
        clone = self._clone_via_pickle(queryset)

        result = list(clone)

        self.assertEqual(result, expected)
        self.assertTrue(result)
        self.assertTrue(all(isinstance(row, dict) for row in result))
        self.assertEqual(result[0]['name'], 'alpha')

    def test_values_list_preserves_tuple_rows(self):
        queryset = NamedCategory.objects.order_by('id').values_list('id', 'name')
        expected = list(queryset)
        clone = self._clone_via_pickle(queryset)

        result = list(clone)

        self.assertEqual(result, expected)
        self.assertTrue(result)
        self.assertTrue(all(isinstance(row, tuple) for row in result))
        self.assertEqual(result[0], expected[0])

    def test_values_list_flat_preserves_scalars(self):
        queryset = NamedCategory.objects.order_by('id').values_list('name', flat=True)
        expected = list(queryset)
        clone = self._clone_via_pickle(queryset)

        result = list(clone)

        self.assertEqual(result, expected)
        self.assertTrue(result)
        self.assertTrue(all(isinstance(row, str) for row in result))
        self.assertEqual(result[0], 'alpha')

    def test_values_list_named_preserves_namedtuples(self):
        queryset = NamedCategory.objects.order_by('id').values_list('id', 'name', named=True)
        expected = list(queryset)
        clone = self._clone_via_pickle(queryset)

        result = list(clone)

        self.assertEqual(result, expected)
        self.assertTrue(result)
        row = result[0]
        self.assertTrue(hasattr(row, '_fields'))
        self.assertEqual(row._fields, expected[0]._fields)
        self.assertEqual(row.name, 'alpha')
