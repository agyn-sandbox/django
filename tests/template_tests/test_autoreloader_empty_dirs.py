from pathlib import Path

from django.template import autoreload
from django.test import SimpleTestCase, override_settings


class TemplateAutoreloadEmptyDirsTests(SimpleTestCase):
    @override_settings(
        TEMPLATES=[
            {
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "DIRS": [""],
                "APP_DIRS": True,
                "OPTIONS": {},
            }
        ]
    )
    def test_empty_string_dirs_are_ignored(self):
        directories = autoreload.get_template_directories()
        self.assertNotIn(Path.cwd(), directories)
