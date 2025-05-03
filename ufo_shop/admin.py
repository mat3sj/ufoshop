from django import forms
from django.contrib import admin
from django.utils.html import format_html
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin

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

    ("Personal info", {"fields": ("first_name", "last_name", "phone")}),

    @admin.register(Item)
    class ItemAdmin(admin.ModelAdmin):
        list_display = ('name', 'merchandiser', 'price', 'amount', 'location', 'category_list', 'is_active',
                        'created_at')
        list_filter = ('is_active', 'location', 'category')
        search_fields = ('name', 'short_description')
        ordering = ('-created_at',)
        # inlines = [PictureInline]
        exclude = ('product_imgs',)

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
    pass


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
    list_display = ('id', 'order', 'item', 'amount')
