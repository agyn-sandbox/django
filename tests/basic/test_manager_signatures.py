import inspect

from django.db import models
from django.test import SimpleTestCase
from django.test.utils import isolate_apps


@isolate_apps("basic")
class ManagerSignatureTests(SimpleTestCase):
    def test_bulk_create_signature_matches_queryset(self):
        class BulkCreateModel(models.Model):
            name = models.CharField(max_length=50)

        manager_signature = inspect.signature(BulkCreateModel.objects.bulk_create)
        queryset_signature = inspect.signature(
            BulkCreateModel.objects.get_queryset().bulk_create
        )
        self.assertEqual(manager_signature, queryset_signature)

    def test_update_or_create_signature_matches_queryset(self):
        class UpdateOrCreateModel(models.Model):
            name = models.CharField(max_length=50)

        manager_signature = inspect.signature(
            UpdateOrCreateModel.objects.update_or_create
        )
        queryset_signature = inspect.signature(
            UpdateOrCreateModel.objects.get_queryset().update_or_create
        )
        self.assertEqual(manager_signature, queryset_signature)
