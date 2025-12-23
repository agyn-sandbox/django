from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone


class RelatedModel(models.Model):
    simple = models.ForeignKey("SimpleModel", models.CASCADE, null=True)


class SimpleModel(models.Model):
    field = models.IntegerField()
    created = models.DateTimeField(default=timezone.now)


class AsyncAuthor(models.Model):
    name = models.CharField(max_length=100)


class AsyncBook(models.Model):
    author = models.ForeignKey(AsyncAuthor, models.CASCADE, related_name="books")
    title = models.CharField(max_length=100)
    pages = models.IntegerField(default=0)


class AsyncGroup(models.Model):
    name = models.CharField(max_length=100)
    members = models.ManyToManyField(
        "AsyncMember",
        through="GroupMembership",
        related_name="groups",
    )


class AsyncMember(models.Model):
    name = models.CharField(max_length=100)
    title = models.CharField(max_length=100, blank=True)


class GroupMembership(models.Model):
    group = models.ForeignKey(AsyncGroup, models.CASCADE)
    member = models.ForeignKey(AsyncMember, models.CASCADE)
    note = models.CharField(max_length=100, blank=True)


class GenericNote(models.Model):
    content_type = models.ForeignKey(ContentType, models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()
    message = models.CharField(max_length=100)
    extra = models.CharField(max_length=100, blank=True)


class GenericArticle(models.Model):
    name = models.CharField(max_length=100)
    notes = GenericRelation(GenericNote, related_query_name="articles")
