from django.core.management import BaseCommand
from django.db import IntegrityError
import logging
from django.contrib.auth.models import User, Group
from django.conf import settings
from ufo_shop.models import *

logger = logging.getLogger(__name__)


def create_shit(model, name, kwargs):
    new_instance, created = model.objects.get_or_create(**kwargs)
    if created:
        logger.info(f'{model.__name__} with name: {name} was created')
    else:
        logger.info(f'{model.__name__} with name: {name} already exists')
    return new_instance


def decorate_model_creation(model):
    logger.info('########################')
    logger.info('Creating %ss', model.__name__)
    logger.info('########################')

class Command(BaseCommand):
    help = f'Create some data in order to play with during the developement'

    def handle(self, *args, **options):

        ###############################################################################
        # Create some users
        ###############################################################################
        decorate_model_creation(User)
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

        ###############################################################################
        # Create some categories
        ###############################################################################
        decorate_model_creation(Category)
        clothes_category = create_shit(Category, 'Oblečení', dict(name='Oblečení'))
        gear_category = create_shit(Category, 'Náčiní', dict(name='Náčiní'))

        ###############################################################################
        # Create some Items
        ###############################################################################
        decorate_model_creation(Item)
        t_shirt = create_shit(Item, 'Tričko s tučňákem', dict(
            name='Tričko s tučňákem',
            merchandiser=admin,
            amount=88,
            short_description='Kvalitní bavlněné tričko s potiskem tučňáka',
            is_active=True,
            description='Pohodlné bavlněné tričko s roztomilým potiskem tučňáka. Vhodné pro každodenní nošení. K dispozici ve všech velikostech.'
        ))

        long_socks = create_shit(Item, 'Fešácký nákolenky', dict(
            name='Fešácký nákolenky',
            merchandiser=admin,
            amount=88,
            short_description='Pohodlné a odolné nákolenky pro Ultimate frisbee',
            is_active=True,
            description='Kvalitní nákolenky speciálně navržené pro Ultimate frisbee. Chrání kolena při skluzech a pádech. Elastický materiál zajišťuje pohodlné nošení. Dostupné ve velikostech S-XL.'
        ))

        ###############################################################################
        # Create some Orders
        ###############################################################################
        decorate_model_creation(Order)
        # Order in cart
        cart_order = create_shit(Order, 'Order in cart', dict(
            user=admin,
            status=1  # In Cart
        ))
        order_item_1 = create_shit(OrderItem, 'Order item 1', dict(
            order=cart_order,
            amount=2,
            item=long_socks
        ))

        # Ordered order
        ordered = create_shit(Order, 'Order ordered', dict(
            user=admin,
            status=2  # Ordered
        ))
        order_item_2 = create_shit(OrderItem, 'Order item 2', dict(
            order=ordered,
            item=long_socks,
            amount=1,
        ))

        # Fulfilled order
        fulfilled = create_shit(Order, 'Order fulfilled', dict(
            user=admin,
            status=3  # Fulfilled
        ))
        order_item_3 = create_shit(OrderItem, 'Order item 3', dict(
            order=fulfilled,
            item=t_shirt,
            amount=3,
        ))
        order_item_4 = create_shit(OrderItem, 'Order item 4', dict(
            order=fulfilled,
            item=long_socks,
            amount=2,
        ))
        logger.info('Fulfilled order was created')
