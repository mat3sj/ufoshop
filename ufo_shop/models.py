
from PIL import Image as PilImage
from io import BytesIO
from django.core.files.base import ContentFile
import os

from django.contrib.auth.models import AbstractUser
from django.db import models

THUMBNAIL_SIZE = 150
SQUARE_IMAGE_SIZE = 1024


class User(AbstractUser):
    phone = models.CharField(max_length=15, verbose_name="Phone Number", blank=True, null=True)
    is_merchandiser = models.BooleanField(default=False, verbose_name="Is Merchandiser")
    # Change the identification field for authentication to 'email'
    email = models.EmailField(unique=True, verbose_name="Email Address")
    username = None

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone']


class Location(models.Model):
    name = models.CharField("Location Name", max_length=50)
    address = models.TextField("Address", default='')
    merchandiser = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Merchandiser")

    class Meta:
        verbose_name = "Location"
        verbose_name_plural = "Locations"

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField("Category Name", max_length=50, unique=True)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class Item(models.Model):
    name = models.CharField("Item Name", max_length=255)
    merchandiser = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Merchandiser")
    price = models.IntegerField("Price", default=0)
    amount = models.IntegerField("Amount", null=True, blank=True)
    location = models.ForeignKey(Location, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Location")
    short_description = models.CharField("Short Description", max_length=255, default='')
    description = models.TextField("Full Description", blank=True, null=True)
    category = models.ManyToManyField('Category', blank=True, verbose_name="Categories")
    is_active = models.BooleanField("Active", default=True)
    created_at = models.DateTimeField("Created At", auto_now_add=True)
    updated_at = models.DateTimeField("Updated At", auto_now=True)

    class Meta:
        verbose_name = "Item"
        verbose_name_plural = "Items"

    def __str__(self):
        return self.name


class Order(models.Model):
    class Status(models.IntegerChoices):
        IN_CART = 1, 'In Cart'
        ORDERED = 2, 'Ordered'
        FULFILLED = 3, 'Fulfilled'

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Customer")
    status = models.IntegerField("Status", choices=Status.choices, default=Status.IN_CART)
    created_at = models.DateTimeField("Created At", auto_now_add=True)
    updated_at = models.DateTimeField("Updated At", auto_now=True)

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"

    def __str__(self):
        return f'{self.user.email} - {self.id} - {self.status}'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, verbose_name="Order")
    item = models.ForeignKey(Item, on_delete=models.CASCADE, verbose_name="Item")
    amount = models.IntegerField("Amount", default=1)
    created_at = models.DateTimeField("Created At", auto_now_add=True)

    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"

    def __str__(self):
        return f'#{self.order.id} {self.item.name} - {self.amount}'


class Picture(models.Model):
    # picture = models.ImageField("Image", upload_to='ufo_shop/static/shop/images/')
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name="pictures",
        verbose_name="Item"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Uploaded by",
        blank=True,
        null=True,
    )
    picture = models.ImageField(
        "Original Image",
        upload_to='item_pictures/originals/'
    )
    thumbnail = models.ImageField(
        "Thumbnail (150x150)",
        upload_to='item_pictures/thumbnails/',
        null=True,
        blank=True
    )
    square_image = models.ImageField(
        "Squared Image (e.g., 500x500)",
        upload_to='item_pictures/squares/',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = "Picture"
        verbose_name_plural = "Pictures"

    def __str__(self):
        # Provide a more descriptive string representation
        if self.item:
            return f"Picture for {self.item.name} ({os.path.basename(self.picture.name)})"
        return os.path.basename(self.picture.name)

    def _check_if_derivatives_needed(self):
        if self.pk:
            try:
                old_instance = Picture.objects.get(pk=self.pk)
                return old_instance.picture != self.picture
            except Picture.DoesNotExist:
                return True  # Should not happen often in save context, but safe
        return True  # New instance

    def generate_square_image(self):
        img = PilImage.open(self.picture)
        square_img = img.copy()
        width, height = square_img.size
        size = min(width, height)

        # Crop to square from center
        left = (width - size) // 2
        top = (height - size) // 2
        right = left + size
        bottom = top + size
        square_img = square_img.crop((left, top, right, bottom))

        # Resize the square crop to the target size
        square_img = square_img.resize((SQUARE_IMAGE_SIZE, SQUARE_IMAGE_SIZE), PilImage.Resampling.LANCZOS)

        # Save square image to buffer
        square_io = BytesIO()
        img_name = os.path.basename(self.picture.name)
        base_name, ext = os.path.splitext(img_name)
        square_img.save(square_io, format=img.format, quality=90)
        square_filename = f"{base_name}_sq{SQUARE_IMAGE_SIZE}{ext}"
        self.square_image.save(square_filename, ContentFile(square_io.getvalue()), save=False)

        return square_img

    def generate_thumbnail(self):
        img = PilImage.open(self.picture)
        img_name = os.path.basename(self.picture.name)
        base_name, ext = os.path.splitext(img_name)

        thumb_size = (THUMBNAIL_SIZE, THUMBNAIL_SIZE)
        thumb_img = img.copy()
        thumb_img.thumbnail(thumb_size, PilImage.Resampling.LANCZOS)

        # Save thumbnail to buffer  
        thumb_io = BytesIO()
        thumb_img.save(thumb_io, format=img.format, quality=85)
        thumb_filename = f"{base_name}_thumb{ext}"
        self.thumbnail.save(thumb_filename, ContentFile(thumb_io.getvalue()), save=False)

    def save(self, *args, **kwargs):
        generate_derivatives = self._check_if_derivatives_needed()

        save_needed_after_derivatives = False
        if generate_derivatives and self.picture:
            temp_skip_derivatives = not self.pk
            if temp_skip_derivatives:
                self.thumbnail = None
                self.square_image = None
            super().save(*args, **kwargs)
            save_needed_after_derivatives = True
        elif not generate_derivatives:
            super().save(*args, **kwargs)

        if generate_derivatives and self.picture and not temp_skip_derivatives:
            try:
                self.generate_square_image()
                self.generate_thumbnail()
                save_needed_after_derivatives = True
            except Exception as e:
                print(f"Error processing image {self.picture.name}: {e}")
                self.thumbnail = None
                self.square_image = None
                save_needed_after_derivatives = True

        if save_needed_after_derivatives:
            update_fields = ['thumbnail', 'square_image']
            if generate_derivatives and not temp_skip_derivatives:
                update_fields.append('picture')

            update_fields = [field for field in update_fields if getattr(self, field) is not None or field == 'picture']

            if self.pk and update_fields:
                kwargs['update_fields'] = update_fields
                super().save(*args, **kwargs)
