from django.db import models
from django.db.models import Q
from django.test import TestCase
from django.test.utils import isolate_apps


class NestedQNoneRenderingTests(TestCase):
    @isolate_apps("db_models")
    def test_nested_q_groups_none_is_null(self):
        class Profile(models.Model):
            bio = models.TextField(null=True, blank=True)

        class Person(models.Model):
            username = models.CharField(max_length=32)
            email = models.EmailField(null=True, blank=True)
            profile = models.ForeignKey(
                "Profile", models.SET_NULL, null=True, blank=True
            )

        condition = Q(username__icontains="john") & (
            Q(profile_id=None) | Q(email=None)
        )
        queryset = Person.objects.filter(condition)

        sql = str(queryset.query)
        self.assertIn("IS NULL", sql)
        self.assertNotIn("= NULL", sql)
        self.assertIn("(", sql)
        self.assertIn(" OR ", sql)
