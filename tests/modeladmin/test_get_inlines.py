from datetime import date
from types import SimpleNamespace
from unittest import mock

from django.contrib.admin.options import ModelAdmin, TabularInline
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory, TestCase

from .models import Band, Concert, Song


class DummyUser(SimpleNamespace):
    def has_perm(self, perm):
        return True


def build_request(username='user'):
    request = RequestFactory().get('/')
    request.user = DummyUser(username=username)
    return request


class ConcertInline(TabularInline):
    model = Concert
    fk_name = 'main_band'


class SongInline(TabularInline):
    model = Song


class GetInlinesHookTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.site = AdminSite()
        cls.band = Band.objects.create(
            name='With inline',
            bio='',
            sign_date=date(1965, 1, 1),
        )

    def test_dynamic_inlines_by_user(self):
        class BandAdmin(ModelAdmin):
            inlines = [ConcertInline, SongInline]

            def get_inlines(self, request, obj=None):
                if request.user.username == 'manager':
                    return [ConcertInline]
                return [SongInline]

        ma = BandAdmin(Band, self.site)

        manager_inlines = ma.get_inline_instances(build_request('manager'))
        staff_inlines = ma.get_inline_instances(build_request('staff'))

        self.assertEqual([inline.__class__ for inline in manager_inlines], [ConcertInline])
        self.assertEqual([inline.__class__ for inline in staff_inlines], [SongInline])

    def test_dynamic_inlines_by_obj_state(self):
        class BandAdmin(ModelAdmin):
            inlines = [ConcertInline]

            def get_inlines(self, request, obj=None):
                if obj and obj.name == 'With inline':
                    return [ConcertInline]
                return []

        ma = BandAdmin(Band, self.site)
        inline_instances = ma.get_inline_instances(build_request(), self.band)
        self.assertEqual([inline.__class__ for inline in inline_instances], [ConcertInline])

        other_band = Band.objects.create(name='Without inline', bio='', sign_date=date(1965, 1, 1))
        inline_instances = ma.get_inline_instances(build_request(), other_band)
        self.assertEqual(inline_instances, [])

    def test_get_inline_instances_uses_get_inlines(self):
        class BandAdmin(ModelAdmin):
            inlines = [ConcertInline]

        ma = BandAdmin(Band, self.site)
        request = build_request()

        with mock.patch.object(ma, 'get_inlines', return_value=[ConcertInline]) as mocked_get_inlines:
            ma.get_inline_instances(request, self.band)

        mocked_get_inlines.assert_called_once_with(request, self.band)

    def test_get_inlines_none_falls_back_to_attribute(self):
        class BandAdmin(ModelAdmin):
            inlines = [ConcertInline]

            def get_inlines(self, request, obj=None):
                return None

        ma = BandAdmin(Band, self.site)
        inline_instances = ma.get_inline_instances(build_request(), self.band)
        self.assertEqual([inline.__class__ for inline in inline_instances], [ConcertInline])

    def test_invalid_inline_type_raises(self):
        class BandAdmin(ModelAdmin):
            inlines = [ConcertInline]

            def get_inlines(self, request, obj=None):
                return [Band]

        ma = BandAdmin(Band, self.site)

        with self.assertRaises(TypeError):
            ma.get_inline_instances(build_request(), self.band)
