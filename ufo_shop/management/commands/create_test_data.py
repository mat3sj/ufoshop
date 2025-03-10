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
        logger.info(f'{model.__name__} "{name}" was created')
    else:
        logger.info(f'{model.__name__} "{name}" already exists')
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
            **{
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

        # Create 'test_merchandiser' if not exists and assign to 'merchandiser' group
        test_merchandiser, created = User.objects.get_or_create(
            **{
                'email': 'test_merchandiser@example.com',
                'is_staff': True,
                'is_active': True,
                'is_merchandiser': True,
            }
        )
        if created and test_merchandiser:
            test_merchandiser.set_password('heslo')
            test_merchandiser.save()
            logger.info("User 'test_merchandiser' was created and assigned to 'merchandiser' group")
        else:
            logger.info("User 'test_merchandiser' already exists")

        # Create 'test_user' if not exists
        test_user, created = User.objects.get_or_create(
            **{
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
            price=499,
            short_description='Kvalitní bavlněné tričko s potiskem tučňáka',
            is_active=True,
            description='Pohodlné bavlněné tričko s roztomilým potiskem tučňáka. Vhodné pro každodenní nošení. K dispozici ve všech velikostech.'
        ))
        t_shirt.category.add(clothes_category)

        long_socks = create_shit(Item, 'Fešácký nákolenky', dict(
            name='Fešácký nákolenky',
            merchandiser=test_merchandiser,
            amount=88,
            price=299,
            short_description='Pohodlné a odolné nákolenky pro Ultimate frisbee',
            is_active=True,
            description='Kvalitní nákolenky speciálně navržené pro Ultimate frisbee. Chrání kolena při skluzech a pádech. Elastický materiál zajišťuje pohodlné nošení. Dostupné ve velikostech S-XL.'
        ))
        long_socks.category.add(clothes_category)

        frisbee = create_shit(Item, 'Ultimate frisbee disk', dict(
            name='Ultimate frisbee disk',
            merchandiser=admin,
            amount=50,
            price=399,
            short_description='Oficiální soutěžní disk pro Ultimate frisbee',
            is_active=True,
            description='Profesionální disk schválený pro soutěžní hru Ultimate frisbee. Vyrobeno z odolného plastu.'
        ))
        frisbee.category.add(gear_category)

        shorts = create_shit(Item, 'Sportovní šortky', dict(
            name='Sportovní šortky',
            merchandiser=test_merchandiser,
            amount=45,
            price=599,
            short_description='Lehké prodyšné šortky',
            is_active=True,
            description='Pohodlné sportovní šortky ideální pro Ultimate frisbee. Rychleschnoucí materiál.'
        ))
        shorts.category.add(clothes_category)

        cap = create_shit(Item, 'Kšiltovka UFO', dict(
            name='Kšiltovka UFO',
            merchandiser=admin,
            amount=30,
            price=349,
            short_description='Stylová kšiltovka s logem UFO',
            is_active=True,
            description='Kvalitní baseballová kšiltovka s vyšitým logem UFO. Nastavitelná velikost.'
        ))
        cap.category.add(clothes_category)

        water_bottle = create_shit(Item, 'Sportovní láhev', dict(
            name='Sportovní láhev',
            merchandiser=test_merchandiser,
            amount=100,
            price=199,
            short_description='Praktická sportovní láhev 0.7l',
            is_active=True,
            description='Odolná sportovní láhev s uzavíratelným pítkem. Objem 0.7l.'
        ))
        water_bottle.category.add(gear_category)

        sweatshirt = create_shit(Item, 'Mikina UFO', dict(
            name='Mikina UFO',
            merchandiser=admin,
            amount=40,
            price=899,
            short_description='Teplá mikina s kapucí',
            is_active=True,
            description='Pohodlná mikina s kapucí a klokaní kapsou. Logo UFO na přední straně.'
        ))
        sweatshirt.category.add(clothes_category)

        wristband = create_shit(Item, 'Potítko', dict(
            name='Potítko',
            merchandiser=test_merchandiser,
            amount=150,
            price=99,
            short_description='Sportovní potítko na zápěstí',
            is_active=True,
            description='Bavlněné potítko s logem UFO. Perfektní pro sport.'
        ))
        wristband.category.add(clothes_category, gear_category)

        backpack = create_shit(Item, 'Sportovní batoh', dict(
            name='Sportovní batoh',
            merchandiser=admin,
            amount=25,
            price=799,
            short_description='Prostorný sportovní batoh',
            is_active=True,
            description='Kvalitní batoh s přihrádkou na disk a nápoje. Objem 30l.'
        ))
        backpack.category.add(gear_category)

        beanie = create_shit(Item, 'Zimní čepice', dict(
            name='Zimní čepice',
            merchandiser=test_merchandiser,
            amount=60,
            price=299,
            short_description='Teplá pletená čepice',
            is_active=True,
            description='Pletená zimní čepice s logem UFO. Příjemný materiál.'
        ))
        beanie.category.add(clothes_category)

        towel = create_shit(Item, 'Sportovní ručník', dict(
            name='Sportovní ručník',
            merchandiser=admin,
            amount=70,
            price=249,
            short_description='Rychleschnoucí ručník',
            is_active=True,
            description='Lehký a skladný sportovní ručník. Rozměry 100x50cm.'
        ))
        towel.category.add(gear_category)

        training_shirt = create_shit(Item, 'Tréninkové tričko', dict(
            name='Tréninkové tričko',
            merchandiser=test_merchandiser,
            amount=80,
            price=449,
            short_description='Funkční tréninkové tričko',
            is_active=True,
            description='Prodyšné sportovní tričko z funkčního materiálu. Ideální na tréninky.'
        ))
        training_shirt.category.add(clothes_category)

        socks = create_shit(Item, 'Sportovní ponožky', dict(
            name='Sportovní ponožky',
            merchandiser=admin,
            amount=120,
            price=149,
            short_description='Komfortní sportovní ponožky',
            is_active=True,
            description='Pohodlné ponožky se zesílenou patou a špičkou. Prodej po párech.'
        ))
        socks.category.add(clothes_category)

        sleeve = create_shit(Item, 'Kompresní rukáv', dict(
            name='Kompresní rukáv',
            merchandiser=test_merchandiser,
            amount=45,
            price=299,
            short_description='Kompresní rukáv na loket',
            is_active=True,
            description='Elastický kompresní rukáv pro podporu při sportu. Chrání před zraněním.'
        ))
        sleeve.category.add(clothes_category, gear_category)

        ###############################################################################
        # Create some Orders
        ###############################################################################
        decorate_model_creation(Order)
        # Order in cart for admin
        cart_order = create_shit(Order, 'Order in cart', dict(
            user=admin,
            status=Order.Status.IN_CART
        ))
        order_item_1 = create_shit(OrderItem, 'Order item 1', dict(
            order=cart_order,
            amount=2,
            item=long_socks
        ))
        order_item_2 = create_shit(OrderItem, 'Order item 2', dict(
            order=cart_order,
            amount=1,
            item=frisbee
        ))

        # Order in cart for test_user
        test_user_cart = create_shit(Order, 'Test user cart', dict(
            user=test_user,
            status=Order.Status.IN_CART
        ))
        order_item_3 = create_shit(OrderItem, 'Order item 3', dict(
            order=test_user_cart,
            item=t_shirt,
            amount=1
        ))
        order_item_4 = create_shit(OrderItem, 'Order item 4', dict(
            order=test_user_cart,
            item=cap,
            amount=1
        ))

        # Ordered orders
        ordered1 = create_shit(Order, 'Order ordered 1', dict(
            user=test_user,
            status=Order.Status.ORDERED
        ))
        order_item_5 = create_shit(OrderItem, 'Order item 5', dict(
            order=ordered1,
            item=backpack,
            amount=1
        ))
        order_item_6 = create_shit(OrderItem, 'Order item 6', dict(
            order=ordered1,
            item=water_bottle,
            amount=2
        ))

        ordered2 = create_shit(Order, 'Order ordered 2', dict(
            user=test_merchandiser,
            status=Order.Status.ORDERED
        ))
        order_item_7 = create_shit(OrderItem, 'Order item 7', dict(
            order=ordered2,
            item=sweatshirt,
            amount=1
        ))

        # Fulfilled orders
        fulfilled1 = create_shit(Order, 'Order fulfilled 1', dict(
            user=admin,
            status=Order.Status.FULFILLED
        ))
        order_item_8 = create_shit(OrderItem, 'Order item 8', dict(
            order=fulfilled1,
            item=t_shirt,
            amount=3
        ))
        order_item_9 = create_shit(OrderItem, 'Order item 9', dict(
            order=fulfilled1,
            item=long_socks,
            amount=2
        ))

        fulfilled2 = create_shit(Order, 'Order fulfilled 2', dict(
            user=test_user,
            status=Order.Status.FULFILLED
        ))
        order_item_10 = create_shit(OrderItem, 'Order item 10', dict(
            order=fulfilled2,
            item=sleeve,
            amount=2
        ))
        order_item_11 = create_shit(OrderItem, 'Order item 11', dict(
            order=fulfilled2,
            item=towel,
            amount=1
        ))
        order_item_12 = create_shit(OrderItem, 'Order item 12', dict(
            order=fulfilled2,
            item=beanie,
            amount=1
        ))
