from django import forms
from django.contrib import admin
from django.utils.html import format_html

from ufo_shop.models import *


class PictureInlineForm(forms.ModelForm):
    model = Picture
    exclude = []

    def __init__(self, *args, **kwargs):
        super(PictureInlineForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['items'].queryset = self.fields['items'].queryset.exclude(pk=self.instance.pk)
        else:
            self.fields['items'].queryset = Item.objects.none()


class PictureInline(admin.TabularInline):
    model = Picture.items.through
    extra = 1  # adjust to your needs


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    inlines = [PictureInline]
    exclude = ('product_imgs',)

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
