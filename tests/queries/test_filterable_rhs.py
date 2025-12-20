from django.db import connection, models
from django.test import TransactionTestCase
from django.test.utils import isolate_apps


@isolate_apps('filterable_rhs')
class RHSFilterableAttributeTests(TransactionTestCase):
    available_apps = []

    def test_fk_rhs_instance_with_filterable_field_does_not_error(self):
        class FilterableType(models.Model):
            filterable = models.BooleanField(default=False)
            name = models.CharField(max_length=50, default='')

            class Meta:
                app_label = 'filterable_rhs'

        class Parent(models.Model):
            ft = models.ForeignKey(FilterableType, models.CASCADE)

            class Meta:
                app_label = 'filterable_rhs'

        with connection.schema_editor() as editor:
            editor.create_model(FilterableType)
            editor.create_model(Parent)
        try:
            ft_false = FilterableType.objects.create(filterable=False, name='false')
            ft_true = FilterableType.objects.create(filterable=True, name='true')
            p1 = Parent.objects.create(ft=ft_false)
            p2 = Parent.objects.create(ft=ft_true)

            # After fix: both filters should work and return expected rows.
            self.assertQuerysetEqual(
                Parent.objects.filter(ft=ft_false).order_by('id'),
                [p1.pk],
                transform=lambda x: x.pk,
            )
            self.assertQuerysetEqual(
                Parent.objects.filter(ft=ft_true).order_by('id'),
                [p2.pk],
                transform=lambda x: x.pk,
            )
        finally:
            with connection.schema_editor() as editor:
                editor.delete_model(Parent)
                editor.delete_model(FilterableType)

    def test_non_expression_values_are_allowed(self):
        class FilterableType(models.Model):
            filterable = models.BooleanField(default=False)
            name = models.CharField(max_length=50, default='')

            class Meta:
                app_label = 'filterable_rhs'

        class Parent(models.Model):
            ft = models.ForeignKey(FilterableType, models.CASCADE)

            class Meta:
                app_label = 'filterable_rhs'

        with connection.schema_editor() as editor:
            editor.create_model(FilterableType)
            editor.create_model(Parent)
        try:
            ft = FilterableType.objects.create(filterable=False, name='x')
            p = Parent.objects.create(ft=ft)
            self.assertEqual(Parent.objects.filter(pk=p.pk).count(), 1)
        finally:
            with connection.schema_editor() as editor:
                editor.delete_model(Parent)
                editor.delete_model(FilterableType)
