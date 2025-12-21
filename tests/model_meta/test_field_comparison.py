from copy import deepcopy

from django.db import models
from django.test import SimpleTestCase
from django.test.utils import isolate_apps


@isolate_apps('model_meta')
class FieldComparisonTests(SimpleTestCase):

    def test_abstract_model_fields_are_distinct(self):
        class AbstractBase(models.Model):
            name = models.CharField(max_length=50)

            class Meta:
                abstract = True

        class ConcreteAlpha(AbstractBase):
            class Meta:
                app_label = 'model_meta'

        class ConcreteBeta(AbstractBase):
            class Meta:
                app_label = 'model_meta'

        alpha_name = ConcreteAlpha._meta.get_field('name')
        beta_name = ConcreteBeta._meta.get_field('name')

        self.assertNotEqual(alpha_name, beta_name)
        self.assertEqual(len({alpha_name, beta_name}), 2)
        self.assertEqual(
            [f.model._meta.label_lower for f in sorted([beta_name, alpha_name])],
            ['model_meta.concretealpha', 'model_meta.concretebeta'],
        )

    def test_same_model_fields_remain_distinct(self):
        class Article(models.Model):
            name = models.CharField(max_length=50)
            title = models.CharField(max_length=50)

            class Meta:
                app_label = 'model_meta'

        name_field = Article._meta.get_field('name')
        title_field = Article._meta.get_field('title')

        self.assertNotEqual(name_field, title_field)
        self.assertLess(name_field, title_field)

    def test_same_model_field_identity(self):
        class Book(models.Model):
            name = models.CharField(max_length=50)

            class Meta:
                app_label = 'model_meta'

        first = Book._meta.get_field('name')
        second = Book._meta.get_field('name')

        self.assertEqual(first, second)
        self.assertEqual(len({first, second}), 1)

    def test_proxy_model_field_matches_concrete(self):
        class Person(models.Model):
            name = models.CharField(max_length=50)

            class Meta:
                app_label = 'model_meta'

        class PersonProxy(Person):
            class Meta:
                app_label = 'model_meta'
                proxy = True

        base_field = Person._meta.get_field('name')
        proxy_field = PersonProxy._meta.get_field('name')

        self.assertEqual(base_field, proxy_field)
        self.assertEqual(len({base_field, proxy_field}), 1)

    def test_unbound_fields(self):
        class Story(models.Model):
            title = models.CharField(max_length=50)

            class Meta:
                app_label = 'model_meta'

        bound_field = Story._meta.get_field('title')

        unbound_field = models.CharField(max_length=50)
        copied_field = deepcopy(unbound_field)

        self.assertEqual(unbound_field, copied_field)
        self.assertNotEqual(bound_field, unbound_field)
        self.assertEqual(len({unbound_field, copied_field}), 1)
