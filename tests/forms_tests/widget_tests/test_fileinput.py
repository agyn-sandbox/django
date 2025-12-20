from django import forms
from django.core.files.base import ContentFile
from django.forms import FileInput
from django.test import SimpleTestCase

from .base import WidgetTest


class FileInputTest(WidgetTest):
    widget = FileInput()

    def test_render(self):
        """
        FileInput widgets never render the value attribute. The old value
        isn't useful if a form is updated or an error occurred.
        """
        self.check_html(self.widget, 'email', 'test@example.com', html='<input type="file" name="email">')
        self.check_html(self.widget, 'email', '', html='<input type="file" name="email">')
        self.check_html(self.widget, 'email', None, html='<input type="file" name="email">')

    def test_value_omitted_from_data(self):
        self.assertIs(self.widget.value_omitted_from_data({}, {}, 'field'), True)
        self.assertIs(self.widget.value_omitted_from_data({}, {'field': 'value'}, 'field'), False)


class FileInputRequiredAttributeTest(SimpleTestCase):

    def test_required_field_without_initial_renders_required(self):
        class FileForm(forms.Form):
            file = forms.FileField(widget=FileInput(), required=True)

        form = FileForm()
        self.assertHTMLEqual(
            str(form['file']),
            '<input type="file" name="file" required id="id_file">',
        )

    def test_required_field_with_initial_omits_required(self):
        class FileForm(forms.Form):
            file = forms.FileField(widget=FileInput(), required=True)

        form = FileForm(initial={'file': ContentFile(b'baz', name='baz.txt')})
        self.assertHTMLEqual(
            str(form['file']),
            '<input type="file" name="file" id="id_file">',
        )

    def test_optional_field_never_renders_required(self):
        class FileForm(forms.Form):
            file = forms.FileField(widget=FileInput(), required=False)

        form = FileForm()
        self.assertHTMLEqual(
            str(form['file']),
            '<input type="file" name="file" id="id_file">',
        )

    def test_explicit_required_attr_is_preserved(self):
        class FileForm(forms.Form):
            file = forms.FileField(
                widget=FileInput(attrs={'required': 'required'}),
                required=False,
            )

        form = FileForm(initial={'file': ContentFile(b'bar', name='bar.txt')})
        self.assertHTMLEqual(
            str(form['file']),
            '<input type="file" name="file" required id="id_file">',
        )

    def test_use_required_attribute_truth_table(self):
        widget = FileInput()
        widget.is_required = True

        self.assertTrue(widget.use_required_attribute(None))
        self.assertTrue(widget.use_required_attribute(''))
        self.assertFalse(widget.use_required_attribute('resume.txt'))
        self.assertFalse(widget.use_required_attribute(ContentFile(b'data', name='cv.pdf')))
