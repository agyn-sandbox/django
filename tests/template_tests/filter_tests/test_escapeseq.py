from django.test import SimpleTestCase
from django.utils.html import mark_safe

from ..utils import setup


class EscapeseqTests(SimpleTestCase):
    @setup({"escapeseq01": '{{ values|escapeseq|join:", " }}'})
    def test_autoescape_on(self):
        output = self.engine.render_to_string(
            "escapeseq01", {"values": ["&", "<"]}
        )
        self.assertEqual(output, "&amp;, &lt;")

    @setup(
        {
            "escapeseq02": (
                '{% autoescape off %}{{ values|join:", " }} -- '
                '{{ values|escapeseq|join:", " }}{% endautoescape %}'
            )
        }
    )
    def test_autoescape_off(self):
        output = self.engine.render_to_string(
            "escapeseq02", {"values": ["&", "<"]}
        )
        self.assertEqual(output, "&, < -- &amp;, &lt;")

    @setup({"escapeseq03": '{{ values|escapeseq|join:", " }}'})
    def test_safe_items_preserved_with_autoescape(self):
        safe_value = mark_safe("<em>safe</em>")
        output = self.engine.render_to_string(
            "escapeseq03", {"values": [safe_value, "<"]}
        )
        self.assertEqual(output, "<em>safe</em>, &lt;")

    @setup(
        {
            "escapeseq04": (
                '{% autoescape off %}{{ values|escapeseq|join:", " }}'
                '{% endautoescape %}'
            )
        }
    )
    def test_safe_items_escaped_with_autoescape_off(self):
        safe_value = mark_safe("<em>safe</em>")
        output = self.engine.render_to_string(
            "escapeseq04", {"values": [safe_value, "<"]}
        )
        self.assertEqual(output, "&lt;em&gt;safe&lt;/em&gt;, &lt;")

    @setup({"escapeseq05": '{{ values|escapeseq|join:", " }}'})
    def test_mixed_types_and_generator(self):
        def value_stream():
            yield "<tag>"
            yield 7
            yield None

        output = self.engine.render_to_string(
            "escapeseq05", {"values": value_stream()}
        )
        self.assertEqual(output, "&lt;tag&gt;, 7, None")

    @setup(
        {
            "escapeseq06": (
                '{% autoescape off %}{{ values|escapeseq|join:sep }}'
                '{% endautoescape %}'
            )
        }
    )
    def test_separator_not_escaped_with_autoescape_off(self):
        output = self.engine.render_to_string(
            "escapeseq06", {"values": ["&", "<"], "sep": "<hr>"}
        )
        self.assertEqual(output, "&amp;<hr>&lt;")
