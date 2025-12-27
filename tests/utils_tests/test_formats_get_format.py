from django.test import SimpleTestCase
from django.utils import formats
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy


class GetFormatTests(SimpleTestCase):
    def setUp(self):
        super().setUp()
        formats.reset_format_cache()
        self.addCleanup(formats.reset_format_cache)

    def test_lazy_literal_format(self):
        self.assertEqual(formats.get_format(gettext_lazy("Y-m-d")), "Y-m-d")

    def test_lazy_setting_lookup(self):
        value = formats.get_format(gettext_lazy("DATE_FORMAT"))
        self.assertIsInstance(value, str)

    def test_bytes_input(self):
        self.assertEqual(formats.get_format(b"Y-m-d"), "Y-m-d")

    def test_non_ascii_literal(self):
        self.assertEqual(formats.get_format("Y年m月d日"), "Y年m月d日")

    def test_safe_string_literal(self):
        self.assertEqual(formats.get_format(mark_safe("Y-m-d")), "Y-m-d")

    def test_protected_type_preserved(self):
        self.assertIsNone(formats.get_format(None, use_l10n=False))
