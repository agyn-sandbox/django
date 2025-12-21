from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import JSONHolder


UNICODE_JSON = ["中国", "España", "😀"]
UNICODE_JSON_TEXT = '["中国", "España", "😀"]'


@override_settings(
    ROOT_URLCONF='admin_views.urls',
    USE_I18N=True,
    USE_L10N=False,
    LANGUAGE_CODE='en',
)
class JSONFieldUnicodeAdminTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(
            username='super',
            email='super@example.com',
            password='secret',
        )
        cls.instance = JSONHolder.objects.create(data=UNICODE_JSON)

    def setUp(self):
        self.client.force_login(self.superuser)

    def test_change_form_displays_unicode(self):
        url = reverse('admin:admin_views_jsonholder_change', args=(self.instance.pk,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        bound_field = response.context['adminform'].form['data']
        rendered_value = bound_field.value()
        self.assertEqual(rendered_value, UNICODE_JSON_TEXT)
        self.assertNotIn('\\u', rendered_value)
        page = response.content.decode()
        self.assertIn('中国', page)
        self.assertIn('España', page)
        self.assertIn('😀', page)

    def test_save_preserves_unicode(self):
        url = reverse('admin:admin_views_jsonholder_change', args=(self.instance.pk,))
        response = self.client.post(url, {'data': UNICODE_JSON_TEXT, '_save': 'Save'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.instance.refresh_from_db()
        self.assertEqual(self.instance.data, UNICODE_JSON)
