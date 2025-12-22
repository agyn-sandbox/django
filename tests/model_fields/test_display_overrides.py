from django.db import models
from django.test import SimpleTestCase


class GetFieldDisplayOverrideTests(SimpleTestCase):

    def test_override_get_field_display_before_field(self):
        class HatBefore(models.Model):
            class Meta:
                app_label = "tests"

            def get_style_display(self):
                return f"before:{self.style}"

            STYLE_CHOICES = [("B", "Bowler"), ("F", "Fedora")]
            style = models.CharField(max_length=1, choices=STYLE_CHOICES)

        self.assertEqual(HatBefore(style="B").get_style_display(), "before:B")

    def test_override_get_field_display_after_field(self):
        class HatAfter(models.Model):
            STYLE_CHOICES = [("B", "Bowler"), ("F", "Fedora")]
            style = models.CharField(max_length=1, choices=STYLE_CHOICES)

            def get_style_display(self):
                return f"after:{self.style}"

            class Meta:
                app_label = "tests"

        self.assertEqual(HatAfter(style="F").get_style_display(), "after:F")

    def test_override__get_FIELD_display_for_specific_field(self):
        class Jacket(models.Model):
            STYLE_CHOICES = [("T", "Trench"), ("P", "Peacoat")]
            style = models.CharField(max_length=1, choices=STYLE_CHOICES)

            class Meta:
                app_label = "tests"

            def _get_FIELD_display(self, field):
                value = super()._get_FIELD_display(field)
                return f"custom:{value}"

        self.assertEqual(Jacket(style="T").get_style_display(), "custom:Trench")

    def test_get_field_display_default_choices_label(self):
        class Scarf(models.Model):
            MATERIAL_CHOICES = [("C", "Cotton")]
            material = models.CharField(max_length=1, choices=MATERIAL_CHOICES, null=True)

            class Meta:
                app_label = "tests"

        scarf = Scarf(material="C")
        self.assertEqual(scarf.get_material_display(), "Cotton")
        scarf.material = "W"
        self.assertEqual(scarf.get_material_display(), "W")
        scarf.material = None
        self.assertIsNone(scarf.get_material_display())
