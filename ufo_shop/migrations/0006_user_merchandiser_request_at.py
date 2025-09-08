from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('ufo_shop', '0005_alter_user_managers'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='merchandiser_request_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Merchandiser request at'),
        ),
    ]
