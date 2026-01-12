from unittest import skipIf

from django.core.exceptions import ValidationError
from django.db import connection, models
from django.test import SimpleTestCase, TestCase

from .models import CharSubclassChoicesModel, Post


class TestCharField(TestCase):

    def test_max_length_passed_to_formfield(self):
        """
        CharField passes its max_length attribute to form fields created using
        the formfield() method.
        """
        cf1 = models.CharField()
        cf2 = models.CharField(max_length=1234)
        self.assertIsNone(cf1.formfield().max_length)
        self.assertEqual(1234, cf2.formfield().max_length)

    def test_lookup_integer_in_charfield(self):
        self.assertEqual(Post.objects.filter(title=9).count(), 0)

    @skipIf(connection.vendor == 'mysql', 'Running on MySQL requires utf8mb4 encoding (#18392)')
    def test_emoji(self):
        p = Post.objects.create(title='Smile 😀', body='Whatever.')
        p.refresh_from_db()
        self.assertEqual(p.title, 'Smile 😀')

    def test_assignment_from_choice_enum(self):
        class Event(models.TextChoices):
            C = 'Carnival!'
            F = 'Festival!'

        p1 = Post.objects.create(title=Event.C, body=Event.F)
        p1.refresh_from_db()
        self.assertEqual(p1.title, 'Carnival!')
        self.assertEqual(p1.body, 'Festival!')
        self.assertEqual(p1.title, Event.C)
        self.assertEqual(p1.body, Event.F)
        p2 = Post.objects.get(title='Carnival!')
        self.assertEqual(p1, p2)
        self.assertEqual(p2.title, Event.C)

    def test_assignment_type_from_textchoices(self):
        class Event(models.TextChoices):
            C = 'Carnival!'
            F = 'Festival!'

        post = Post(body='Festival!')
        post.title = Event.C
        self.assertIs(type(post.title), str)
        self.assertEqual(post.title, 'Carnival!')
        post.save()
        post.refresh_from_db()
        self.assertIs(type(post.title), str)
        self.assertEqual(post.title, 'Carnival!')

    def test_assignment_from_textchoices_on_field_subclasses(self):
        class SampleChoices(models.TextChoices):
            SLUG = 'release-candidate'
            EMAIL = 'contact@example.com'
            URL = 'https://example.com/docs'
            CI = 'CaseInsensitive'

        entry = CharSubclassChoicesModel()
        entry.slug = SampleChoices.SLUG
        self.assertIs(type(entry.slug), str)
        self.assertEqual(entry.slug, 'release-candidate')
        self.assertEqual(entry.slug, SampleChoices.SLUG)
        entry.email = SampleChoices.EMAIL
        self.assertIs(type(entry.email), str)
        self.assertEqual(entry.email, 'contact@example.com')
        self.assertEqual(entry.email, SampleChoices.EMAIL)
        entry.url = SampleChoices.URL
        self.assertIs(type(entry.url), str)
        self.assertEqual(entry.url, 'https://example.com/docs')
        self.assertEqual(entry.url, SampleChoices.URL)
        entry.ci_label = SampleChoices.CI
        self.assertIs(type(entry.ci_label), str)
        self.assertEqual(entry.ci_label, 'CaseInsensitive')
        self.assertEqual(entry.ci_label, SampleChoices.CI)
        entry.save()
        entry.refresh_from_db()
        self.assertIs(type(entry.slug), str)
        self.assertEqual(entry.slug, SampleChoices.SLUG)
        self.assertIs(type(entry.email), str)
        self.assertEqual(entry.email, SampleChoices.EMAIL)
        self.assertIs(type(entry.url), str)
        self.assertEqual(entry.url, SampleChoices.URL)
        self.assertIs(type(entry.ci_label), str)
        self.assertEqual(entry.ci_label, SampleChoices.CI)

    def test_assignment_type_from_str(self):
        post = Post(title='Carnival!', body='Festival!')
        self.assertIs(type(post.title), str)
        self.assertEqual(post.title, 'Carnival!')
        post.save()
        post.refresh_from_db()
        self.assertIs(type(post.title), str)
        self.assertEqual(post.title, 'Carnival!')


class ValidationTests(SimpleTestCase):

    class Choices(models.TextChoices):
        C = 'c', 'C'

    def test_charfield_raises_error_on_empty_string(self):
        f = models.CharField()
        with self.assertRaises(ValidationError):
            f.clean('', None)

    def test_charfield_cleans_empty_string_when_blank_true(self):
        f = models.CharField(blank=True)
        self.assertEqual('', f.clean('', None))

    def test_charfield_with_choices_cleans_valid_choice(self):
        f = models.CharField(max_length=1, choices=[('a', 'A'), ('b', 'B')])
        self.assertEqual('a', f.clean('a', None))

    def test_charfield_with_choices_raises_error_on_invalid_choice(self):
        f = models.CharField(choices=[('a', 'A'), ('b', 'B')])
        with self.assertRaises(ValidationError):
            f.clean('not a', None)

    def test_enum_choices_cleans_valid_string(self):
        f = models.CharField(choices=self.Choices.choices, max_length=1)
        self.assertEqual(f.clean('c', None), 'c')

    def test_enum_choices_invalid_input(self):
        f = models.CharField(choices=self.Choices.choices, max_length=1)
        with self.assertRaises(ValidationError):
            f.clean('a', None)

    def test_charfield_raises_error_on_empty_input(self):
        f = models.CharField(null=False)
        with self.assertRaises(ValidationError):
            f.clean(None, None)
