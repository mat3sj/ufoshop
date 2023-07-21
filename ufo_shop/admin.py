from django import forms
from django.contrib import admin


from ufo_shop.models import Item, Picture, Category, Location


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
    pass


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    pass


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    pass
