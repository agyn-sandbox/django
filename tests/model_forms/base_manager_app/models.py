from django.db import models


class PublishedArticleManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_archived=False)


class Article(models.Model):
    is_archived = models.BooleanField(default=False)

    objects = PublishedArticleManager()
    all_objects = models.Manager()

    class Meta:
        app_label = 'model_forms_fk_validate'
        base_manager_name = 'all_objects'


class FavoriteArticles(models.Model):
    article = models.ForeignKey('model_forms_fk_validate.Article', models.CASCADE)

    class Meta:
        app_label = 'model_forms_fk_validate'
