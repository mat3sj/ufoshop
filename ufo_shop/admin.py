from django import forms
from django.contrib import admin, messages
from django.utils.html import format_html
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django.utils.safestring import mark_safe

from ufo_shop.models import *


@admin.register(User)
class UserAdmin(DefaultUserAdmin):
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "phone")}),
        ("Permissions",
         {"fields": ("is_active", "is_staff", "is_superuser", 'is_merchandiser', "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "is_staff", "is_active", 'is_merchandiser'),
            },
        ),
    )
    list_display = ("email", "first_name", "last_name", "is_staff", 'is_merchandiser', 'is_superuser')
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)


class PictureInlineForm(forms.ModelForm):
    model = Picture
    exclude = []

    def __init__(self, *args, **kwargs):
        super(PictureInlineForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['items'].queryset = self.fields['items'].queryset.exclude(pk=self.instance.pk)
        else:
            self.fields['items'].queryset = Item.objects.none()


#
# class PictureInline(admin.StackedInline):
#     model = Picture
#     extra = 1


# Define the inline admin for Pictures
class PictureInline(admin.TabularInline):  # Use TabularInline for a compact view
    model = Picture
    extra = 1  # Show 1 extra empty form for adding new pictures
    fields = ('picture', 'thumbnail_preview',)  # Fields to display in the inline form
    readonly_fields = ('thumbnail_preview',)  # Make the preview read-only

    def thumbnail_preview(self, obj):
        # Display a small preview of the thumbnail if it exists
        if obj.thumbnail:
            # Adjust width/height as needed for preview size
            return mark_safe(f'<img src="{obj.thumbnail.url}" width="100" />')
        return "No thumbnail generated yet"  # Placeholder if thumbnail doesn't exist

    thumbnail_preview.short_description = 'Thumbnail Preview'  # Column header


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'merchandiser', 'price', 'amount', 'locations_list', 'category_list', 'is_active',
                    'created_at')
    list_filter = ('is_active', 'category')
    search_fields = ('name', 'short_description')
    ordering = ('-created_at',)
    inlines = [PictureInline]
    exclude = ('product_imgs',)

    def locations_list(self, obj):
        return ", ".join([location.name for location in obj.locations.all()])

    locations_list.short_description = 'Pickup Locations'

    def category_list(self, obj):
        return ", ".join([category.name for category in obj.category.all()])

    category_list.short_description = 'Categories'

    def get_queryset(self, request):
        """
        Customize the queryset of items displayed in the admin.
        Restrict to items created by the logged-in user if the user
        belongs to the "Merchandiser" group.
        """
        qs = super().get_queryset(request)
        # Check if the user is in the "Merchandiser" group
        if request.user.groups.filter(name="Merchandiser").exists():
            return qs.filter(merchandiser=request.user)
        return qs

    def save_model(self, request, obj, form, change):
        """
        Automatically set the `merchandiser` field (creator) to the logged-in user
        when saving an item.
        """
        if not change:  # For new objects
            obj.merchandiser = request.user
        super().save_model(request, obj, form, change)




@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', '_items')

    def _items(self, obj):
        count = obj.item_set.count()
        url = f"/admin/ufo_shop/item/?category__id__exact={obj.id}"
        return format_html('<a href="{}">{} ({})</a>', url, "Items", count)

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'merchandiser', 'is_universal')
    list_filter = ('is_universal', 'merchandiser')
    search_fields = ('name', 'address')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', 'user', 'status', '_items_link')

    def _items_link(self, obj):
        count = obj.orderitem_set.count()
        url = f"/admin/ufo_shop/orderitem/?order__id__exact={obj.id}"
        return format_html('<a href="{}">{} ({})</a>', url, "Items", count)

    _items_link.short_description = 'Items'


@admin.register(OrderItem)
class OrderItemtAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'item', 'amount', 'pickup_location')


@admin.register(Picture)
class PictureAdmin(admin.ModelAdmin):
    list_display = (
        'item_link',
        'uploaded_by_user',
        'original_image_preview',
        'thumbnail_preview',
        'square_image_preview',
    )
    list_filter = ('item', 'user')
    search_fields = (
        'item__name',
        'user__username',
        'user__email',
        'picture__icontains'  # Search by original picture filename
    )
    readonly_fields = (
        'original_image_preview_inline',
        'thumbnail_preview_inline',
        'square_image_preview_inline',
        'item_link_inline',  # If you want to show it in the detail view as well
        'user_link_inline',  # If you want to show it in the detail view as well
    )
    fields = (  # Define the order and fields for the detail/edit view
        'item',
        'user',
        'picture',
        'original_image_preview_inline',
        'thumbnail_preview_inline',
        'square_image_preview_inline',
    )
    actions = ['create_thumbnail_action', 'create_square_image_action']

    def get_queryset(self, request):
        # Eager load related item and user to prevent N+1 queries
        return super().get_queryset(request).select_related('item', 'user')

    def _image_preview(self, obj_field, alt_text="Image Preview", width="100"):
        if obj_field:
            return mark_safe(f'<img src="{obj_field.url}" width="{width}" alt="{alt_text}" />')
        return "N/A"

    def original_image_preview(self, obj):
        return self._image_preview(obj.picture, "Original Image Preview")

    original_image_preview.short_description = 'Original'

    def thumbnail_preview(self, obj):
        return self._image_preview(obj.thumbnail, "Thumbnail Preview")

    thumbnail_preview.short_description = 'Thumbnail'

    def square_image_preview(self, obj):
        return self._image_preview(obj.square_image, "Square Image Preview")

    square_image_preview.short_description = 'Square'

    # For previews within the Picture detail admin page
    def original_image_preview_inline(self, obj):
        return self._image_preview(obj.picture, "Original Image Preview", width="300")

    original_image_preview_inline.short_description = 'Original Image Preview'

    def thumbnail_preview_inline(self, obj):
        return self._image_preview(obj.thumbnail, "Thumbnail Preview", width="150")

    thumbnail_preview_inline.short_description = 'Thumbnail Preview'

    def square_image_preview_inline(self, obj):
        return self._image_preview(obj.square_image, "Square Image Preview", width="200")

    square_image_preview_inline.short_description = 'Square Image Preview'

    def item_link(self, obj):
        if obj.item:
            from django.urls import reverse
            link = reverse("admin:ufo_shop_item_change", args=[obj.item.id])
            return mark_safe(f'<a href="{link}">{obj.item.name}</a>')
        return "N/A"

    item_link.short_description = 'Associated Item'
    item_link.admin_order_field = 'item'  # Allows sorting by item

    def uploaded_by_user(self, obj):
        if obj.user:
            # Assuming you have a User admin, otherwise just display username
            from django.urls import reverse
            try:
                link = reverse("admin:auth_user_change", args=[obj.user.id])  # Default User admin
                return mark_safe(f'<a href="{link}">{obj.user.username}</a>')
            except:  # In case the user model admin is different or not registered under 'auth'
                return obj.user.username
        return "N/A"

    uploaded_by_user.short_description = 'Uploaded By'
    uploaded_by_user.admin_order_field = 'user'  # Allows sorting by user

    # Inline versions for the detail view if needed
    def item_link_inline(self, obj):
        return self.item_link(obj)

    item_link_inline.short_description = 'Associated Item'

    def user_link_inline(self, obj):
        return self.uploaded_by_user(obj)

    user_link_inline.short_description = 'Uploaded By'

    def create_thumbnail_action(self, request, queryset):
        processed_count = 0
        for picture in queryset:
            try:
                # Assuming your Picture model has a method 'generate_thumbnail'
                picture.generate_thumbnail()
                processed_count += 1
            except AttributeError:
                self.message_user(request, f"Picture object {picture.id} does not have a 'generate_thumbnail' method.",
                                  messages.ERROR)
                return
            except Exception as e:
                self.message_user(request, f"Error generating thumbnail for {picture.id}: {e}", messages.ERROR)
        if processed_count > 0:
            self.message_user(request, f"Successfully generated thumbnails for {processed_count} pictures.",
                              messages.SUCCESS)

    create_thumbnail_action.short_description = "Create Thumbnail(s)"

    def create_square_image_action(self, request, queryset):
        processed_count = 0
        for picture in queryset:
            try:
                # Assuming your Picture model has a method 'generate_square_image'
                picture.generate_square_image()
                processed_count += 1
            except AttributeError:
                self.message_user(request,
                                  f"Picture object {picture.id} does not have a 'generate_square_image' method.",
                                  messages.ERROR)
                return
            except Exception as e:
                self.message_user(request, f"Error generating square image for {picture.id}: {e}", messages.ERROR)
        if processed_count > 0:
            self.message_user(request, f"Successfully generated square images for {processed_count} pictures.",
                              messages.SUCCESS)

    create_square_image_action.short_description = "Create Square Image(s)"


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'published_at', 'is_active')
    list_filter = ('is_active', 'published_at')
    search_fields = ('title', 'content')
    ordering = ('-published_at',)

    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="100" />')
        return "No image"

    image_preview.short_description = 'Image Preview'

    readonly_fields = ('image_preview',)
    fields = ('title', 'content', 'image', 'image_preview', 'is_active')


@admin.register(Issuer)
class IssuerAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'country', 'registration_id', 'tax_id', 'is_default')
    list_filter = ('is_default', 'country')
    search_fields = ('name', 'address', 'registration_id', 'tax_id')
    ordering = ('name',)

    def logo_preview(self, obj):
        if obj.logo:
            return mark_safe(f'<img src="{obj.logo.url}" width="100" />')
        return "No logo"

    logo_preview.short_description = 'Logo Preview'

    readonly_fields = ('logo_preview',)
    fields = (
        'name', 'address', 'city', 'postal_code', 'country',
        'registration_id', 'tax_id', 'bank_account', 'iban', 'swift',
        'logo', 'logo_preview', 'is_default'
    )


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'invoice_number', 'order', 'issuer', 'created_at', 'due_date', 'is_paid', 'total_amount')
    list_filter = ('is_paid', 'issuer', 'created_at')
    search_fields = ('invoice_number', 'order__id', 'order__user__email')
    ordering = ('-created_at',)
    actions = ['generate_pdf_action', 'regenerate_pdf_action']

    readonly_fields = ('pdf_preview', 'created_at', 'updated_at')

    def pdf_preview(self, obj):
        if obj.pdf_file:
            return mark_safe(f'<a href="{obj.pdf_file.url}" target="_blank">View PDF</a>')
        return "No PDF generated"

    pdf_preview.short_description = 'PDF Preview'

    fields = (
        'invoice_number', 'order', 'issuer', 'created_at', 'updated_at',
        'is_paid', 'due_date', 'total_amount', 'currency', 'pdf_file', 'pdf_preview'
    )

    def generate_pdf_action(self, request, queryset):
        generated_count = 0
        for invoice in queryset:
            if not invoice.pdf_file:
                invoice.generate_pdf()
                generated_count += 1

        if generated_count > 0:
            self.message_user(request, f"Successfully generated PDF for {generated_count} invoice(s).", messages.SUCCESS)
        else:
            self.message_user(request, "No PDFs were generated. All selected invoices already have PDFs.", messages.INFO)

    generate_pdf_action.short_description = "Generate PDF if not generated"
    
    def regenerate_pdf_action(self, request, queryset):
        regenerated_count = 0
        for invoice in queryset:
            try:
                # Regenerate PDF regardless of whether it already exists
                success = invoice.generate_pdf()
                if success:
                    regenerated_count += 1
                else:
                    self.message_user(request, f"Failed to regenerate PDF for invoice {invoice.invoice_number}.", messages.ERROR)
            except Exception as e:
                self.message_user(request, f"Error regenerating PDF for invoice {invoice.invoice_number}: {e}", messages.ERROR)
        
        if regenerated_count > 0:
            self.message_user(request, f"Successfully regenerated PDF for {regenerated_count} invoice(s).", messages.SUCCESS)
        else:
            self.message_user(request, "No PDFs were regenerated. Please check for errors.", messages.WARNING)
    
    regenerate_pdf_action.short_description = "Regenerate PDF (even if already exists)"

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Generate PDF if it doesn't exist
        if not obj.pdf_file:
            obj.generate_pdf()
