from django.db import models


class Product(models.Model):
    name = models.CharField(max_length=255)
    color = models.CharField(max_length=32, null=True)
    price = models.IntegerField(null=True)
    discounted_price = models.IntegerField(null=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(price__gt=models.F('discounted_price')),
                name='price_gt_discounted_price',
            ),
            models.UniqueConstraint(fields=['name', 'color'], name='name_color_uniq'),
            models.UniqueConstraint(
                fields=['name'],
                name='name_without_color_uniq',
                condition=models.Q(color__isnull=True),
            ),
        ]


class MixedCheck(models.Model):
    first_value = models.IntegerField()
    second_value = models.IntegerField()
    third_value = models.IntegerField(null=True)
    fourth_value = models.IntegerField()
    flag = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(first_value__gt=models.F('second_value')) | (
                        models.Q(third_value__isnull=False)
                        & models.Q(fourth_value__lt=models.F('second_value'))
                    )
                )
                & models.Q(flag=True),
                name='mixed_or_and_check',
            ),
            models.UniqueConstraint(
                fields=['first_value', 'flag'],
                name='mixed_or_and_unique',
                condition=(
                    models.Q(third_value__gt=models.F('fourth_value'))
                    | (
                        models.Q(second_value__lte=models.F('fourth_value'))
                        & models.Q(third_value__isnull=True)
                    )
                ),
            ),
        ]
