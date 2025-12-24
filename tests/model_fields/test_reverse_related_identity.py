from django.db import models
from django.test import SimpleTestCase
from django.test.utils import isolate_apps


class ManyToManyRelIdentityTests(SimpleTestCase):
    @isolate_apps('model_fields')
    def test_through_fields_list_is_hashable(self):
        class Parent(models.Model):
            pass

        class ParentProxy(Parent):
            class Meta:
                proxy = True

        class Container(models.Model):
            m2m = models.ManyToManyField(
                ParentProxy,
                through='Through',
                through_fields=['container', 'parent'],
            )

        class Through(models.Model):
            container = models.ForeignKey(Container, on_delete=models.CASCADE)
            parent = models.ForeignKey(Parent, on_delete=models.CASCADE)

        rel = Container._meta.get_field('m2m').remote_field
        self.assertIsInstance(hash(rel), int)
