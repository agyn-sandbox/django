"""
OR lookups

To perform an OR lookup, or a lookup that combines ANDs and ORs, combine
``QuerySet`` objects using ``&`` and ``|`` operators.

Alternatively, use positional arguments, and pass one or more expressions of
clauses using the variable ``django.db.models.Q``.
"""

from django.db import models


class Article(models.Model):
    headline = models.CharField(max_length=50)
    pub_date = models.DateTimeField()

    class Meta:
        ordering = ('pub_date',)

    def __str__(self):
        return self.headline


class Author(models.Model):
    code = models.CharField(max_length=20, unique=True)
    active = models.BooleanField(default=False)

    class Meta:
        ordering = ('id',)

    def __str__(self):
        return self.code


class Book(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='books')
    pages = models.IntegerField()

    class Meta:
        ordering = ('id',)


class CodeBook(models.Model):
    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE,
        related_name='code_books',
        to_field='code',
    )
    pages = models.IntegerField()

    class Meta:
        ordering = ('id',)
