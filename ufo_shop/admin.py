from django.contrib import admin


from ufo_shop.models import Item, Picture, Category, Location


class PictureInline(admin.StackedInline):
    model = Picture


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    inlines = [PictureInline]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    pass


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    pass
