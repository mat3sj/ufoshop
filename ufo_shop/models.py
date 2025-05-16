
from PIL import Image as PilImage, ImageDraw
from io import BytesIO
from django.core.files.base import ContentFile
import os
import qrcode
import base64
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

    class Meta:
        verbose_name = "Item"
        verbose_name_plural = "Items"

    def __str__(self):
        return self.name


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
