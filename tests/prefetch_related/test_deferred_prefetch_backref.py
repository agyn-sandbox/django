from pathlib import Path

from django.apps import AppConfig
from django.db import connection, models
from django.db.models import Prefetch
from django.test import TransactionTestCase
from django.test.utils import CaptureQueriesContext, isolate_apps


class RegressConfig(AppConfig):
    name = 'tests.prefetch_related.test_deferred_prefetch_backref'
    label = 'regress'
    path = str(Path(__file__).resolve().parent)

    def import_models(self):
        # Models are defined dynamically within isolated tests.
        self.models = self.apps.all_models[self.label]


class DeferredNestedPrefetchTests(TransactionTestCase):
    available_apps = []

    def _create_models(self, *models):
        with connection.constraint_checks_disabled():
            with connection.schema_editor(atomic=False) as editor:
                for model in models:
                    editor.create_model(model)

    def _delete_models(self, *models):
        with connection.constraint_checks_disabled():
            with connection.schema_editor(atomic=False) as editor:
                for model in models:
                    editor.delete_model(model)

    @isolate_apps('tests.prefetch_related.test_deferred_prefetch_backref.RegressConfig')
    def test_onetoone_nested_prefetch_backref_deferred(self):
        class SimpleUser(models.Model):
            email = models.CharField(max_length=255)
            KIND_CHOICES = ((0, 'basic'), (1, 'pro'))
            kind = models.IntegerField(choices=KIND_CHOICES, default=0)

            class Meta:
                app_label = 'regress'

        class SimpleProfile(models.Model):
            full_name = models.CharField(max_length=255)
            user = models.OneToOneField(SimpleUser, models.CASCADE, related_name='profile')

            class Meta:
                app_label = 'regress'

        self.addCleanup(self._delete_models, SimpleProfile, SimpleUser)
        self._create_models(SimpleUser, SimpleProfile)

        u = SimpleUser.objects.create(email='u@example.com', kind=1)
        SimpleProfile.objects.create(full_name='User One', user=u)

        qs = SimpleUser.objects.only('email').prefetch_related(
            Prefetch(
                'profile',
                queryset=SimpleProfile.objects.prefetch_related(
                    Prefetch('user', queryset=SimpleUser.objects.only('kind'))
                ),
            )
        )
        users = list(qs)
        inner_user = users[0].profile.user
        # kind should not trigger a query
        with self.assertNumQueries(0):
            _ = inner_user.kind
        # email should be deferred and trigger a query when accessed
        with self.assertNumQueries(1):
            _ = inner_user.email
        self.assertNotIn('kind', inner_user.get_deferred_fields())

    @isolate_apps('tests.prefetch_related.test_deferred_prefetch_backref.RegressConfig')
    def test_foreignkey_nested_prefetch_backref_deferred(self):
        class SimpleUser(models.Model):
            email = models.CharField(max_length=255)
            KIND_CHOICES = ((0, 'basic'), (1, 'pro'))
            kind = models.IntegerField(choices=KIND_CHOICES, default=0)

            class Meta:
                app_label = 'regress'

        class SimpleProfile(models.Model):
            full_name = models.CharField(max_length=255)
            user = models.ForeignKey(SimpleUser, models.CASCADE)

            class Meta:
                app_label = 'regress'

        self.addCleanup(self._delete_models, SimpleProfile, SimpleUser)
        self._create_models(SimpleUser, SimpleProfile)

        u = SimpleUser.objects.create(email='u@example.com', kind=1)
        SimpleProfile.objects.create(full_name='User One', user=u)

        qs = SimpleUser.objects.only('email').prefetch_related(
            Prefetch(
                'simpleprofile_set',
                queryset=SimpleProfile.objects.prefetch_related(
                    Prefetch('user', queryset=SimpleUser.objects.only('kind'))
                ),
            )
        )
        users = list(qs)
        with CaptureQueriesContext(connection) as ctx:
            profiles = list(users[0].simpleprofile_set.all())
        self.assertEqual(len(ctx.captured_queries), 0)

        p = profiles[0]
        with self.assertNumQueries(0):
            _ = p.user.kind
        with self.assertNumQueries(1):
            _ = p.user.email
        self.assertNotIn('kind', p.user.get_deferred_fields())
