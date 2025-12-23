from datetime import datetime
from operator import attrgetter
import re

from django.db.models import Q
from django.test import TestCase

from .models import Article, Author, Book, CodeBook


class OrLookupsTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.a1 = Article.objects.create(
            headline='Hello', pub_date=datetime(2005, 11, 27)
        ).pk
        cls.a2 = Article.objects.create(
            headline='Goodbye', pub_date=datetime(2005, 11, 28)
        ).pk
        cls.a3 = Article.objects.create(
            headline='Hello and goodbye', pub_date=datetime(2005, 11, 29)
        ).pk

    def test_filter_or(self):
        self.assertQuerysetEqual(
            (
                Article.objects.filter(headline__startswith='Hello') |
                Article.objects.filter(headline__startswith='Goodbye')
            ), [
                'Hello',
                'Goodbye',
                'Hello and goodbye'
            ],
            attrgetter("headline")
        )

        self.assertQuerysetEqual(
            Article.objects.filter(headline__contains='Hello') | Article.objects.filter(headline__contains='bye'), [
                'Hello',
                'Goodbye',
                'Hello and goodbye'
            ],
            attrgetter("headline")
        )

        self.assertQuerysetEqual(
            Article.objects.filter(headline__iexact='Hello') | Article.objects.filter(headline__contains='ood'), [
                'Hello',
                'Goodbye',
                'Hello and goodbye'
            ],
            attrgetter("headline")
        )

        self.assertQuerysetEqual(
            Article.objects.filter(Q(headline__startswith='Hello') | Q(headline__startswith='Goodbye')), [
                'Hello',
                'Goodbye',
                'Hello and goodbye'
            ],
            attrgetter("headline")
        )

    def test_stages(self):
        # You can shorten this syntax with code like the following,  which is
        # especially useful if building the query in stages:
        articles = Article.objects.all()
        self.assertQuerysetEqual(
            articles.filter(headline__startswith='Hello') & articles.filter(headline__startswith='Goodbye'),
            []
        )
        self.assertQuerysetEqual(
            articles.filter(headline__startswith='Hello') & articles.filter(headline__contains='bye'), [
                'Hello and goodbye'
            ],
            attrgetter("headline")
        )

    def test_pk_q(self):
        self.assertQuerysetEqual(
            Article.objects.filter(Q(pk=self.a1) | Q(pk=self.a2)), [
                'Hello',
                'Goodbye'
            ],
            attrgetter("headline")
        )

        self.assertQuerysetEqual(
            Article.objects.filter(Q(pk=self.a1) | Q(pk=self.a2) | Q(pk=self.a3)), [
                'Hello',
                'Goodbye',
                'Hello and goodbye'
            ],
            attrgetter("headline"),
        )

    def test_pk_in(self):
        self.assertQuerysetEqual(
            Article.objects.filter(pk__in=[self.a1, self.a2, self.a3]), [
                'Hello',
                'Goodbye',
                'Hello and goodbye'
            ],
            attrgetter("headline"),
        )

        self.assertQuerysetEqual(
            Article.objects.filter(pk__in=(self.a1, self.a2, self.a3)), [
                'Hello',
                'Goodbye',
                'Hello and goodbye'
            ],
            attrgetter("headline"),
        )

        self.assertQuerysetEqual(
            Article.objects.filter(pk__in=[self.a1, self.a2, self.a3, 40000]), [
                'Hello',
                'Goodbye',
                'Hello and goodbye'
            ],
            attrgetter("headline"),
        )

    def test_q_repr(self):
        or_expr = Q(baz=Article(headline="Foö"))
        self.assertEqual(repr(or_expr), "<Q: (AND: ('baz', <Article: Foö>))>")
        negated_or = ~Q(baz=Article(headline="Foö"))
        self.assertEqual(repr(negated_or), "<Q: (NOT (AND: ('baz', <Article: Foö>)))>")

    def test_q_negated(self):
        # Q objects can be negated
        self.assertQuerysetEqual(
            Article.objects.filter(Q(pk=self.a1) | ~Q(pk=self.a2)), [
                'Hello',
                'Hello and goodbye'
            ],
            attrgetter("headline")
        )

        self.assertQuerysetEqual(
            Article.objects.filter(~Q(pk=self.a1) & ~Q(pk=self.a2)), [
                'Hello and goodbye'
            ],
            attrgetter("headline"),
        )
        # This allows for more complex queries than filter() and exclude()
        # alone would allow
        self.assertQuerysetEqual(
            Article.objects.filter(Q(pk=self.a1) & (~Q(pk=self.a2) | Q(pk=self.a3))), [
                'Hello'
            ],
            attrgetter("headline"),
        )

    def test_complex_filter(self):
        # The 'complex_filter' method supports framework features such as
        # 'limit_choices_to' which normally take a single dictionary of lookup
        # arguments but need to support arbitrary queries via Q objects too.
        self.assertQuerysetEqual(
            Article.objects.complex_filter({'pk': self.a1}), [
                'Hello'
            ],
            attrgetter("headline"),
        )

        self.assertQuerysetEqual(
            Article.objects.complex_filter(Q(pk=self.a1) | Q(pk=self.a2)), [
                'Hello',
                'Goodbye'
            ],
            attrgetter("headline"),
        )

    def test_empty_in(self):
        # Passing "in" an empty list returns no results ...
        self.assertQuerysetEqual(
            Article.objects.filter(pk__in=[]),
            []
        )
        # ... but can return results if we OR it with another query.
        self.assertQuerysetEqual(
            Article.objects.filter(Q(pk__in=[]) | Q(headline__icontains='goodbye')), [
                'Goodbye',
                'Hello and goodbye'
            ],
            attrgetter("headline"),
        )

    def test_q_and(self):
        # Q arg objects are ANDed
        self.assertQuerysetEqual(
            Article.objects.filter(Q(headline__startswith='Hello'), Q(headline__contains='bye')), [
                'Hello and goodbye'
            ],
            attrgetter("headline")
        )
        # Q arg AND order is irrelevant
        self.assertQuerysetEqual(
            Article.objects.filter(Q(headline__contains='bye'), headline__startswith='Hello'), [
                'Hello and goodbye'
            ],
            attrgetter("headline"),
        )

        self.assertQuerysetEqual(
            Article.objects.filter(Q(headline__startswith='Hello') & Q(headline__startswith='Goodbye')),
            []
        )

    def test_q_exclude(self):
        self.assertQuerysetEqual(
            Article.objects.exclude(Q(headline__startswith='Hello')), [
                'Goodbye'
            ],
            attrgetter("headline")
        )

    def test_other_arg_queries(self):
        # Try some arg queries with operations other than filter.
        self.assertEqual(
            Article.objects.get(Q(headline__startswith='Hello'), Q(headline__contains='bye')).headline,
            'Hello and goodbye'
        )

        self.assertEqual(
            Article.objects.filter(Q(headline__startswith='Hello') | Q(headline__contains='bye')).count(),
            3
        )

        self.assertSequenceEqual(
            Article.objects.filter(Q(headline__startswith='Hello'), Q(headline__contains='bye')).values(), [
                {"headline": "Hello and goodbye", "id": self.a3, "pub_date": datetime(2005, 11, 29)},
            ],
        )

        self.assertEqual(
            Article.objects.filter(Q(headline__startswith='Hello')).in_bulk([self.a1, self.a2]),
            {self.a1: Article.objects.get(pk=self.a1)}
        )


class RelatedInOrLookupSingleColumnTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.active_author = Author.objects.create(code='ACTIVE', active=True)
        cls.inactive_author = Author.objects.create(code='INACTIVE', active=False)
        cls.other_inactive_author = Author.objects.create(code='OTHER', active=False)

        cls.pk_books = {
            'active': Book.objects.create(author=cls.active_author, pages=320),
            'zero_pages': Book.objects.create(author=cls.inactive_author, pages=0),
            'inactive': Book.objects.create(author=cls.other_inactive_author, pages=640),
        }

        cls.code_books = {
            'active': CodeBook.objects.create(author=cls.active_author, pages=320),
            'zero_pages': CodeBook.objects.create(author=cls.inactive_author, pages=0),
            'inactive': CodeBook.objects.create(author=cls.other_inactive_author, pages=640),
        }

    def _assert_subquery_selects_single_column(self, queryset, expected_column):
        compiler = queryset.query.get_compiler(using=queryset.db)
        sql, params = compiler.as_sql()
        match = re.search(r'IN\s*\(\s*SELECT\s+(.+?)\s+FROM', sql, flags=re.IGNORECASE | re.DOTALL)
        self.assertIsNotNone(match, msg=sql)
        select_expression = match.group(1)
        self.assertNotIn(',', select_expression)
        normalized = re.sub(r'["`\[\]]', '', select_expression).lower()
        self.assertIn(expected_column.lower(), normalized)

    def test_related_in_rhs_uses_single_pk_column(self):
        active_authors = Author.objects.filter(active=True)
        queryset = Book.objects.filter(
            Q(author__in=active_authors) | Q(pages=0)
        ).order_by('pk')

        expected = Book.objects.filter(
            Q(author__in=Author.objects.filter(active=True).values_list('pk', flat=True)) |
            Q(pages=0)
        ).order_by('pk')

        self.assertEqual(list(queryset), list(expected))
        self.assertEqual(
            list(queryset.values_list('pk', flat=True)),
            [
                self.pk_books['active'].pk,
                self.pk_books['zero_pages'].pk,
            ],
        )
        self._assert_subquery_selects_single_column(queryset, Author._meta.pk.column)

    def test_related_in_rhs_uses_single_to_field_column(self):
        active_authors = Author.objects.filter(active=True)
        queryset = CodeBook.objects.filter(
            Q(author__in=active_authors) | Q(pages=0)
        ).order_by('pk')

        expected = CodeBook.objects.filter(
            Q(author__in=Author.objects.filter(active=True).values_list('code', flat=True)) |
            Q(pages=0)
        ).order_by('pk')

        self.assertEqual(list(queryset), list(expected))
        self.assertEqual(
            list(queryset.values_list('pk', flat=True)),
            [
                self.code_books['active'].pk,
                self.code_books['zero_pages'].pk,
            ],
        )
        self._assert_subquery_selects_single_column(queryset, Author._meta.get_field('code').column)
