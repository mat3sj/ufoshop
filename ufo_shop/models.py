from django.contrib.auth.models import User
from django.db import models


class Location(models.Model):
    name = models.CharField(max_length=50)
    address = models.TextField(default='')
    merchandiser = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class Item(models.Model):
    name = models.CharField(max_length=255)
    merchandiser = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.IntegerField(null=True, blank=True)
    location = models.ForeignKey(Location, on_delete=models.CASCADE, null=True, blank=True)
    short_description = models.CharField(max_length=255, default='')
    description = models.TextField(blank=True, null=True)
    category = models.ManyToManyField('Category', blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Order(models.Model):
    class Status(models.IntegerChoices):
        IN_CART = 1
        ORDERED = 2
        FULFILLED = 3

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.IntegerField(choices=Status.choices, default=Status.IN_CART)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.email} - {self.id} - {self.status}'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    amount = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'#{self.order.id} {self.item.name} - {self.amount}'


class Picture(models.Model):
    picture = models.ImageField(upload_to='ufo_shop/static/shop/images/')
    items = models.ManyToManyField(Item, blank=True, related_name="product_imgs")

    def __str__(self):
        return self.picture.url
