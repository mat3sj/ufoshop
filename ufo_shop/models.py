
from PIL import Image as PilImage, ImageDraw
from io import BytesIO
from django.core.files.base import ContentFile
import os
import qrcode
import base64
import math
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import HorizontalBarsDrawer
from qrcode.image.styles.moduledrawers.pil import RoundedModuleDrawer

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.html import mark_safe

THUMBNAIL_SIZE = 150
SQUARE_IMAGE_SIZE = 1024

# Bank account details for QR code payment
BANK_ACCOUNT = {
    'account_number': '670100-2210457032/6210',
    'currency': 'CZK',
}


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
    is_universal = models.BooleanField("Universal Location", default=False, 
                                      help_text="If checked, this location will be available for all merchandisers")
    note = models.TextField("Additional Note", blank=True, null=True)

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
    locations = models.ManyToManyField(Location, blank=True, verbose_name="Pickup Locations")
    short_description = models.CharField("Short Description", max_length=255, default='')
    description = models.TextField("Full Description", blank=True, null=True)
    category = models.ManyToManyField('Category', blank=True, verbose_name="Categories")
    is_active = models.BooleanField("Active", default=True)
    created_at = models.DateTimeField("Created At", auto_now_add=True)
    updated_at = models.DateTimeField("Updated At", auto_now=True)
    # For color variants grouping
    parent_item = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, 
                                   related_name='variants', verbose_name="Parent Item")
    is_variant = models.BooleanField("Is Variant", default=False)
    color = models.CharField("Color", max_length=50, blank=True, null=True)

    class Meta:
        verbose_name = "Item"
        verbose_name_plural = "Items"

    def __str__(self):
        if self.color and self.is_variant:
            return f"{self.name} - {self.color}"
        return self.name

    def get_variants(self):
        """Get all color variants for this item"""
        if self.is_variant and self.parent_item:
            # If this is a variant, get siblings from the parent
            return self.parent_item.variants.all()
        else:
            # If this is a parent, get all variants
            return self.variants.all()

    def has_variants(self):
        """Check if this item has color variants"""
        return self.variants.exists()


class Order(models.Model):
    class Status(models.IntegerChoices):
        IN_CART = 1, 'In Cart'
        ORDERED = 2, 'Ordered'
        PAID = 3, 'Paid'
        SHIPPED = 4, 'Shipped'
        FULFILLED = 5, 'Fulfilled'
        CANCELLED = 6, 'Cancelled'

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Customer")
    status = models.IntegerField("Status", choices=Status.choices, default=Status.IN_CART)

    # Shipping information
    shipping_address = models.TextField("Shipping Address", blank=True, null=True)
    shipping_city = models.CharField("City", max_length=100, blank=True, null=True)
    shipping_state = models.CharField("State/Province", max_length=100, blank=True, null=True)
    shipping_country = models.CharField("Country", max_length=100, blank=True, null=True)
    shipping_zip = models.CharField("ZIP/Postal Code", max_length=20, blank=True, null=True)

    # Contact information
    contact_email = models.EmailField("Contact Email", blank=True, null=True)
    contact_phone = models.CharField("Contact Phone", max_length=20, blank=True, null=True)

    # Payment information
    payment_method = models.CharField("Payment Method", max_length=50, blank=True, null=True)
    payment_id = models.CharField("Payment ID", max_length=100, blank=True, null=True)
    needs_receipt = models.BooleanField("Needs Receipt", default=False, help_text="If checked, a 7% fee will be added for receipt processing")
    receipt_fee = models.DecimalField("Receipt Fee", max_digits=10, decimal_places=2, default=0)

    # Order details
    subtotal = models.DecimalField("Subtotal", max_digits=10, decimal_places=2, default=0)
    shipping_cost = models.DecimalField("Shipping Cost", max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField("Total", max_digits=10, decimal_places=2, default=0)

    # Timestamps
    created_at = models.DateTimeField("Created At", auto_now_add=True)
    updated_at = models.DateTimeField("Updated At", auto_now=True)
    paid_at = models.DateTimeField("Paid At", blank=True, null=True)
    shipped_at = models.DateTimeField("Shipped At", blank=True, null=True)
    fulfilled_at = models.DateTimeField("Fulfilled At", blank=True, null=True)

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"

    def __str__(self):
        return f'{self.user.email} - {self.id} - {self.status}'

    def calculate_totals(self):
        """Calculate subtotal and total for the order"""
        order_items = self.orderitem_set.all()
        self.subtotal = sum(item.item.price * item.amount for item in order_items)
        # For now, shipping is free
        self.shipping_cost = 0

        # Calculate receipt fee if needed (7% of subtotal)
        self.receipt_fee = 0
        if self.needs_receipt:
            self.receipt_fee = self.subtotal * 0.07

        self.total = self.subtotal + self.shipping_cost + self.receipt_fee
        return self.total

    def _convert_to_iban(self, account_number):
        """
        Convert Czech bank account number to IBAN format
        Format: CZ + check digits + bank code (4 digits) + account number (up to 16 digits)
        """
        # Split account number into parts
        parts = account_number.split('/')
        if len(parts) != 2:
            # If the format is not as expected, return the original account number
            return account_number

        account_prefix_number, bank_code = parts

        # Remove any hyphens from the account number
        account_prefix_number = account_prefix_number.replace('-', '')

        # Pad the account number with leading zeros to make it 16 digits
        account_number_padded = account_prefix_number.zfill(16)

        # Prepare the IBAN without check digits
        # For Czech Republic, the BBAN (Basic Bank Account Number) is bank_code + account_number_padded
        bban = f"{bank_code}{account_number_padded}"

        # Rearrange the country code and add '00' as placeholder for check digits
        # Convert letters to numbers: A=10, B=11, ..., Z=35
        # For 'CZ', C=12, Z=35
        rearranged = f"{bban}123500"  # 'CZ' converted to digits (12, 35) + '00'

        # Calculate the check digits using mod-97
        # Since the number might be too large for int conversion, we'll calculate mod-97 in chunks
        remainder = 0
        for i in range(0, len(rearranged), 6):
            chunk = rearranged[i:i+6]
            remainder = (remainder * 10**len(chunk) + int(chunk)) % 97

        # Calculate the check digits
        check_digits = str(98 - remainder).zfill(2)

        # Construct the final IBAN
        iban = f"CZ{check_digits}{bban}"

        return iban

    def get_payment_qr_code(self):
        """Generate a stylish QR code for payment with rounded dots"""
        if not self.id:
            return None

        # Create QR code data
        account_number = BANK_ACCOUNT['account_number']
        # Convert account number to IBAN format
        iban = self._convert_to_iban(account_number)
        amount = float(self.total)
        currency = BANK_ACCOUNT['currency']
        message = f"Order #{self.id} - {self.contact_email}"
        variable_symbol = str(self.id)


        # Format the QR code data according to the Czech QR payment standard
        qr_data = f"SPD*1.0*ACC:{iban}*AM:{amount:.2f}*CC:{currency}*MSG:{message}*X-VS:{variable_symbol}*RN:Mates-UfoShop"

        # Create QR code with custom settings for rounded dots and medium error correction
        qr = qrcode.QRCode(
            version=None,  # Allow automatic version selection based on data size
            error_correction=qrcode.constants.ERROR_CORRECT_M,  # Medium error correction for smaller size
            box_size=6,  # Smaller box size for a more compact QR code
            border=2,  # Minimum recommended border
            image_factory=StyledPilImage,  # Use StyledPilImage for custom styling
        )
        qr.add_data(qr_data)
        qr.make(fit=True)

        # Generate the QR code image with rounded modules
        img = qr.make_image(
            module_drawer=HorizontalBarsDrawer(),  # Use RoundedModuleDrawer for rounded dots
            fill_color="black",
            back_color="white"
        )

        # Convert to base64 for embedding in HTML
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        return mark_safe(f'<img src="data:image/png;base64,{img_str}" alt="Payment QR Code" class="img-fluid">')


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, verbose_name="Order")
    item = models.ForeignKey(Item, on_delete=models.CASCADE, verbose_name="Item")
    amount = models.IntegerField("Amount", default=1)
    pickup_location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Pickup Location")
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
            return f"Picture for {self.item.name} ({os.path.basename(self.picture.name if self.picture else (self.thumbnail.name if self.thumbnail else self.square_image.name))})"
        return os.path.basename(self.picture.name if self.picture else (self.thumbnail.name if self.thumbnail else self.square_image.name))

    def delete(self, *args, **kwargs):
        # Store paths to image files
        thumbnail_path = self.thumbnail.path if self.thumbnail else None
        square_image_path = self.square_image.path if self.square_image else None
        picture_path = self.picture.path if self.picture else None

        # Delete the model instance
        super().delete(*args, **kwargs)

        # Delete the image files from storage
        if thumbnail_path and os.path.exists(thumbnail_path):
            os.remove(thumbnail_path)

        if square_image_path and os.path.exists(square_image_path):
            os.remove(square_image_path)

        if picture_path and os.path.exists(picture_path):
            os.remove(picture_path)

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
        # self.square_image=square_img
        # self.save()
        self.square_image.save(square_filename, ContentFile(square_io.getvalue()), save=True)


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
        self.thumbnail.save(thumb_filename, ContentFile(thumb_io.getvalue()), save=True)

    def resize_large_image(self):
        """Resize image if it's larger than 2MB"""
        if not self.picture:
            return

        # Check file size (2MB = 2 * 1024 * 1024 bytes)
        MAX_SIZE = 2 * 1024 * 1024
        if self.picture.size > MAX_SIZE:
            img = PilImage.open(self.picture)

            # Calculate new dimensions while maintaining aspect ratio
            width, height = img.size
            ratio = min(1.0, math.sqrt(MAX_SIZE / self.picture.size))
            new_width = int(width * ratio)
            new_height = int(height * ratio)

            # Resize the image
            resized_img = img.resize((new_width, new_height), PilImage.Resampling.LANCZOS)

            # Save resized image to buffer
            img_io = BytesIO()
            img_format = img.format if img.format else 'JPEG'
            resized_img.save(img_io, format=img_format, quality=90)

            # Replace the original image with the resized one
            img_name = os.path.basename(self.picture.name)
            self.picture.save(img_name, ContentFile(img_io.getvalue()), save=True)

            return True
        return False

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Store original force_insert and force_update values
        force_insert = kwargs.pop('force_insert', False)
        force_update = kwargs.pop('force_update', False)

        generate_derivatives = self._check_if_derivatives_needed()
        # is_new_instance = not self.pk
        if not self.thumbnail:
            self.generate_thumbnail()
        if not self.square_image:
            self.generate_square_image()

        # # First save to get a pk if this is a new instance
        # if is_new_instance:
        #     # For new instances, always use force_insert=True
        #     super().save(*args, **{**kwargs, 'force_insert': True})
        #
        # # Check and resize large images
        # resized = False
        # if generate_derivatives and self.picture:
        #     resized = self.resize_large_image()
        #
        # # Generate derivatives if needed
        # save_needed_after_derivatives = False
        # derivatives_success = False
        # if generate_derivatives and self.picture:
        #     try:
        #         self.generate_square_image()
        #         self.generate_thumbnail()
        #         save_needed_after_derivatives = True
        #         derivatives_success = True
        #     except Exception as e:
        #         print(f"Error processing image {self.picture.name}: {e}")
        #         self.thumbnail = None
        #         self.square_image = None
        #         save_needed_after_derivatives = True
        #
        # # For subsequent saves, we're always updating (not inserting)
        # if not is_new_instance:
        #     # Save again if derivatives were generated or image was resized
        #     if save_needed_after_derivatives or resized:
        #         update_fields = ['thumbnail', 'square_image']
        #         if resized:
        #             update_fields.append('picture')
        #
        #         update_fields = [field for field in update_fields if getattr(self, field) is not None or field == 'picture']
        #
        #         if update_fields:
        #             # For updates, use update_fields and force_update=True
        #             super().save(*args, **{**kwargs, 'update_fields': update_fields, 'force_update': True})
        #     elif not generate_derivatives:
        #         # If we're not generating derivatives and this is not a new instance
        #         super().save(*args, **{**kwargs, 'force_update': True})
        #
        # # Delete the original large image if derivatives were successfully created
        # if derivatives_success and self.thumbnail and self.square_image:
        #     # Store the path to the original image
        #     original_path = self.picture.path
        #
        #     # Clear the picture field in the model
        #     self.picture = None
        #
        #     # Save the model to update the database
        #     if is_new_instance:
        #         super().save(*args, **{**kwargs, 'update_fields': ['picture'], 'force_update': True})
        #     else:
        #         super().save(*args, **{**kwargs, 'update_fields': ['picture'], 'force_update': True})
        #
        #     # Delete the file from storage if it exists
        #     if os.path.exists(original_path):
        #         os.remove(original_path)


class News(models.Model):
    title = models.CharField("Title", max_length=200)
    content = models.TextField("Content")
    image = models.ImageField("Image", upload_to='news_images/', blank=True, null=True)
    published_at = models.DateTimeField("Published At", auto_now_add=True)
    is_active = models.BooleanField("Active", default=True)

    class Meta:
        verbose_name = "News"
        verbose_name_plural = "News"
        ordering = ['-published_at']

    def __str__(self):
        return self.title
