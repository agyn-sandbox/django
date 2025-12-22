from django.db import models


class MyBigAutoField(models.BigAutoField):
    pass


class MySmallAutoField(models.SmallAutoField):
    pass
