# Generated by Django 4.2.3 on 2025-03-06 17:45

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("ufo_shop", "0003_item_category_item_created_at_item_is_active_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="itemincart",
            name="amount",
        ),
        migrations.RemoveField(
            model_name="itemincart",
            name="category",
        ),
        migrations.RemoveField(
            model_name="itemincart",
            name="created_at",
        ),
        migrations.RemoveField(
            model_name="itemincart",
            name="description",
        ),
        migrations.RemoveField(
            model_name="itemincart",
            name="is_active",
        ),
        migrations.RemoveField(
            model_name="itemincart",
            name="location",
        ),
        migrations.RemoveField(
            model_name="itemincart",
            name="name",
        ),
        migrations.RemoveField(
            model_name="itemincart",
            name="short_description",
        ),
        migrations.RemoveField(
            model_name="itemincart",
            name="supplier",
        ),
        migrations.RemoveField(
            model_name="itemincart",
            name="updated_at",
        ),
    ]
