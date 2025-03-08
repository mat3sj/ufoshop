from django.core.management import BaseCommand
from django.db import IntegrityError
import logging
from django.contrib.auth.models import User, Group
from django.conf import settings
from ufo_shop.models import *

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = f'Create some data in order to play with during the developement'

    def handle(self, *args, **options):
        # Create categories
        user = User.objects.get(pk=1)
        try:
            Category.objects.create(name='Oblečení')
            logger.info('Category %s was created', 'Oblečení')
            Category.objects.create(name='Náčiní')
            logger.info('Category %s was created', 'Náčiní')

        except IntegrityError:
            pass

        if not Item.objects.filter(name='Tričko s tučňákem').exists():
            t_shirt = Item.objects.create(
                name='Tričko s tučňákem',
                merchandiser=user,
                amount=88,
                short_description='Kvalitní bavlněné tričko s potiskem tučňáka',
                is_active=True,
                description='Pohodlné bavlněné tričko s roztomilým potiskem tučňáka. Vhodné pro každodenní nošení. K dispozici ve všech velikostech.'
            )
            t_shirt.category.add(Category.objects.get(name='Oblečení'))
            logger.info('Item %s was created', 'Tričko s tučňákem')

        if not Item.objects.filter(name='Fešácký nákolenky').exists():
            pads = Item.objects.create(
                name='Fešácký nákolenky',
                merchandiser=user,
                amount=88,
                short_description='Pohodlné a odolné nákolenky pro Ultimate frisbee',
                is_active=True,
                description='Kvalitní nákolenky speciálně navržené pro Ultimate frisbee. Chrání kolena při skluzech a pádech. Elastický materiál zajišťuje pohodlné nošení. Dostupné ve velikostech S-XL.'
            )
            pads.category.add(Category.objects.get(name='Náčiní'))
            logger.info('Item %s was created', 'Fešácký nákolenky')
        # Create test orders
        # Order in cart
        if not Order.objects.filter(user=user, status=1).exists():
            cart_order = Order.objects.create(
                user=user,
                status=1  # In Cart
            )
            OrderItem.objects.create(
                order=cart_order,
                amount=2,
                item=Item.objects.get(name='Fešácký nákolenky')
            )
            logger.info('Order in cart was created')

        # Ordered order
        if not Order.objects.filter(user=user, status=2).exists():
            ordered = Order.objects.create(
                user=user,
                status=2  # Ordered
            )
            OrderItem.objects.create(
                order=ordered,
                item=Item.objects.get(name='Fešácký nákolenky'),
                amount=1,
            )
            logger.info('Ordered order was created')

        # Fulfilled order  
        if not Order.objects.filter(user=user, status=3).exists():
            fulfilled = Order.objects.create(
                user=user,
                status=3  # Fulfilled
            )
            OrderItem.objects.create(
                order=fulfilled,
                item=Item.objects.get(name='Tričko s tučňákem'),
                amount=3,
            )
            OrderItem.objects.create(
                order=fulfilled,
                item=Item.objects.get(name='Fešácký nákolenky'),
                amount=2,
            )
            logger.info('Fulfilled order was created')

        ###############################################################################
        # Create some users
        ###############################################################################

        admin, created = User.objects.get_or_create(
            username=settings.SUPERUSER_NAME,
            defaults={
                'email': settings.SUPERUSER_EMAIL,
                'is_staff': True,
                'is_superuser': True,
                'is_active': True
            }
        )
        if created:
            admin.set_password(settings.SUPERUSER_PASS)
            admin.save()
            logger.info("Superuser '%s' was created", settings.SUPERUSER_NAME)
        else:
            logger.info("Superuser '%s' already exists", settings.SUPERUSER_NAME)

        merchandiser_group, created = Group.objects.get_or_create(name='Merchandiser')
        # Create 'test_merchandiser' if not exists and assign to 'merchandiser' group
        test_merchandiser, created = User.objects.get_or_create(
            username='test_merchandiser',
            defaults={
                'email': 'test_merchandiser@example.com',
                'is_staff': True,
                'is_active': True
            }
        )
        if created:
            test_merchandiser.set_password('heslo')
            test_merchandiser.save()
            test_merchandiser.groups.add(merchandiser_group)
            logger.info("User 'test_merchandiser' was created and assigned to 'merchandiser' group")
        else:
            logger.info("User 'test_merchandiser' already exists")

        # Create 'test_user' if not exists
        test_user, created = User.objects.get_or_create(
            username='test_user',
            defaults={
                'email': 'test_user@example.com',
                'is_active': True
            }
        )
        if created:
            test_user.set_password('heslo')
            test_user.save()
            logger.info("User 'test_user' was created")
        else:
            logger.info("User 'test_user' already exists")
