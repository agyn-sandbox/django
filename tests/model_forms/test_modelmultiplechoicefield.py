from django import forms
from django.test import TestCase, skipUnlessDBFeature

from .models import Article, Category, Writer


@skipUnlessDBFeature('supports_select_union')
class ModelMultipleChoiceFieldUnionQuerysetTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category_one = Category.objects.create(
            name='Entertainment',
            slug='entertainment',
            url='entertainment',
        )
        cls.category_two = Category.objects.create(
            name='A test',
            slug='a-test',
            url='test',
        )
        cls.writer = Writer.objects.create(name='Reporter')

    def test_empty_submission_uses_none_queryset(self):
        union_queryset = Category.objects.filter(pk=self.category_one.pk).union(
            Category.objects.filter(pk=self.category_two.pk),
        )

        class ArticleCategoriesForm(forms.ModelForm):
            categories = forms.ModelMultipleChoiceField(
                queryset=union_queryset,
                required=False,
            )

            class Meta:
                model = Article
                fields = ['headline', 'slug', 'pub_date', 'writer', 'article', 'categories']

        form = ArticleCategoriesForm(data={
            'headline': 'Union article',
            'slug': 'union-article',
            'pub_date': '2024-01-01',
            'writer': self.writer.pk,
            'article': 'Content',
            'categories': [],
        })
        self.assertTrue(form.is_valid())
        article = form.save()
        self.assertEqual(article.categories.count(), 0)
