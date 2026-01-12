import uuid

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import SubThingUUIDFK, ThingWithUUID


@override_settings(ROOT_URLCONF="admin_views.urls")
class InlineUUIDToFieldTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(
            username="super", password="secret", email="super@example.com"
        )

    def setUp(self):
        self.client.force_login(self.superuser)

    def test_inline_fk_to_uuid_uses_parent_default(self):
        constant_uuid = uuid.UUID("00000000-0000-0000-0000-000000000001")
        uuid_field = ThingWithUUID._meta.get_field("uuid")
        original_default = uuid_field.default
        uuid_field.default = lambda: constant_uuid
        self.addCleanup(setattr, uuid_field, "default", original_default)

        add_url = reverse("admin:admin_views_thingwithuuid_add")
        response = self.client.get(add_url)
        self.assertEqual(response.status_code, 200)

        inline_formset = response.context["inline_admin_formsets"][0].formset
        management_data = {
            f"{inline_formset.prefix}-{key}": str(value)
            for key, value in inline_formset.management_form.initial.items()
        }
        management_data[f"{inline_formset.prefix}-TOTAL_FORMS"] = "1"
        management_data[f"{inline_formset.prefix}-INITIAL_FORMS"] = "0"

        post_data = {
            "name": "Parent",
            f"{inline_formset.prefix}-0-id": "",
            f"{inline_formset.prefix}-0-thing": str(constant_uuid),
            f"{inline_formset.prefix}-0-name": "Child",
            "_save": "Save",
        }
        post_data.update(management_data)

        response = self.client.post(add_url, post_data)
        self.assertEqual(response.status_code, 302)

        parent = ThingWithUUID.objects.get()
        child = SubThingUUIDFK.objects.get()
        self.assertIsNotNone(parent.uuid)
        self.assertEqual(parent.uuid, constant_uuid)
        self.assertEqual(child.thing_id, constant_uuid)
