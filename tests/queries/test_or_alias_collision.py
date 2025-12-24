from django.db import connection, models
from django.db.models import Q
from django.test import TestCase
from django.test.utils import isolate_apps


@isolate_apps('queries', attr_name='apps')
class OrAliasCollisionTests(TestCase):
    @classmethod
    def setUpClass(cls):
        class Baz(models.Model):
            name = models.CharField(max_length=50, blank=True)

            class Meta:
                app_label = 'queries'

        class Foo(models.Model):
            name = models.CharField(max_length=50, blank=True)

            class Meta:
                app_label = 'queries'

        class Bar(models.Model):
            foo = models.ForeignKey(Foo, related_name='bars', on_delete=models.CASCADE)
            baz = models.ForeignKey(Baz, related_name='bars', on_delete=models.CASCADE)

            class Meta:
                app_label = 'queries'

        class OtherBar(models.Model):
            foo = models.ForeignKey(Foo, related_name='other_bars', on_delete=models.CASCADE)
            baz = models.ForeignKey(Baz, related_name='other_bars', on_delete=models.CASCADE)

            class Meta:
                app_label = 'queries'

        class Qux(models.Model):
            foos = models.ManyToManyField(Foo, related_name='quxes')
            bazes = models.ManyToManyField(Baz, related_name='quxes')

            class Meta:
                app_label = 'queries'

        cls.Baz = Baz
        cls.Foo = Foo
        cls.Bar = Bar
        cls.OtherBar = OtherBar
        cls.Qux = Qux
        cls._created_models = [Baz, Foo, Bar, OtherBar, Qux]
        with connection.schema_editor() as editor:
            for model in cls._created_models:
                editor.create_model(model)
        try:
            super().setUpClass()
        except Exception:
            with connection.schema_editor() as editor:
                for model in reversed(cls._created_models):
                    editor.delete_model(model)
            raise
        cls.addClassCleanup(cls._tearDownModels)

    @classmethod
    def setUpTestData(cls):
        Baz = cls.Baz
        Foo = cls.Foo
        Bar = cls.Bar
        OtherBar = cls.OtherBar
        Qux = cls.Qux

        baz = Baz.objects.create(name='B1')
        foo = Foo.objects.create(name='Foo 1')
        Bar.objects.create(foo=foo, baz=baz)
        OtherBar.objects.create(foo=foo, baz=baz)
        qux = Qux.objects.create()
        qux.foos.add(foo)
        qux.bazes.add(baz)

        cls.baz = baz
        cls.foo = foo
        cls.qux = qux

    @classmethod
    def _tearDownModels(cls):
        with connection.schema_editor() as editor:
            for model in reversed(cls._created_models):
                editor.delete_model(model)

    def test_or_combine_avoids_alias_collision(self):
        Foo = self.Foo
        qux = self.qux
        bazes = qux.bazes.all()

        qs1 = qux.foos.all()
        qs2 = Foo.objects.filter(
            Q(bars__baz__in=bazes) | Q(other_bars__baz__in=bazes)
        )

        combined_12 = qs1 | qs2
        combined_21 = qs2 | qs1

        combined_12_ids = list(combined_12.order_by('pk').values_list('pk', flat=True))
        combined_21_ids = list(combined_21.order_by('pk').values_list('pk', flat=True))

        expected_ids = [self.foo.pk]
        self.assertSequenceEqual(combined_12_ids, expected_ids)
        self.assertSequenceEqual(combined_21_ids, expected_ids)
        self.assertSequenceEqual(combined_12_ids, combined_21_ids)
