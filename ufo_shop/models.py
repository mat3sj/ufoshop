from django.contrib.auth.models import User
from django.db import models


class Item(models.Model):
    name = models.CharField(max_length=255)
    supplier = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Picture(models.Model):
    picture = models.ImageField(upload_to='ufo_shop/static/shop/images/')
    items = models.ManyToManyField(Item, blank=True, related_name="product_imgs")

    def __str__(self):
        return self.picture.url


class Category(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Location(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name
