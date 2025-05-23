# Generated by Django 5.1.7 on 2025-05-15 22:15

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ufo_shop", "0007_order_needs_receipt_order_receipt_fee"),
    ]

    operations = [
        migrations.CreateModel(
            name="News",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=200, verbose_name="Title")),
                ("content", models.TextField(verbose_name="Content")),
                (
                    "image",
                    models.ImageField(
                        blank=True,
                        null=True,
                        upload_to="news_images/",
                        verbose_name="Image",
                    ),
                ),
                (
                    "published_at",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Published At"
                    ),
                ),
                ("is_active", models.BooleanField(default=True, verbose_name="Active")),
            ],
            options={
                "verbose_name": "News",
                "verbose_name_plural": "News",
                "ordering": ["-published_at"],
            },
        ),
    ]
