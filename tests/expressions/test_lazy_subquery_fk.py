import sys
import types

from django.db import connection, models
from django.db.models import OuterRef, Subquery
from django.test import TransactionTestCase
from django.test.utils import isolate_apps
from django.utils.functional import SimpleLazyObject


class LazyObjectNestedSubqueryFKTests(TransactionTestCase):
    databases = {"default"}
    available_apps = None

    def test_lazy_object_nested_subquery_foreign_key(self):
        module_name = "expressions_tests"
        module = types.ModuleType(module_name)
        module.__file__ = __file__
        sys.modules[module_name] = module
        self.addCleanup(lambda: sys.modules.pop(module_name, None))

        with isolate_apps(module_name):

            class Employee(models.Model):
                name = models.CharField(max_length=100)

                class Meta:
                    app_label = "expressions_tests"

            class Company(models.Model):
                name = models.CharField(max_length=100)
                ceo = models.ForeignKey(Employee, on_delete=models.CASCADE)

                class Meta:
                    app_label = "expressions_tests"

            with connection.schema_editor() as editor:
                editor.create_model(Employee)
                editor.create_model(Company)

            def cleanup():
                with connection.schema_editor() as editor:
                    editor.delete_model(Company)
                    editor.delete_model(Employee)

            self.addCleanup(cleanup)

            ceo = Employee.objects.create(name="Alice")
            company = Company.objects.create(name="ACME", ceo=ceo)

            lazy_ceo = SimpleLazyObject(lambda: Employee.objects.get(pk=ceo.pk))

            inner_ceo = Subquery(
                Company.objects.filter(pk=OuterRef("pk")).values("ceo")[:1]
            )
            nested_ceo = Subquery(
                Company.objects.filter(pk=OuterRef("pk"))
                .annotate(inner=inner_ceo)
                .values("inner")[:1]
            )

            qs = Company.objects.annotate(nested_ceo=nested_ceo).filter(
                nested_ceo=lazy_ceo
            )

            self.assertEqual(list(qs), [company])
            self.assertIs(
                qs.query.annotations["nested_ceo"].output_field,
                Employee._meta.get_field("id"),
            )
