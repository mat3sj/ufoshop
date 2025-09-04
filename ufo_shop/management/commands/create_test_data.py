from django.core.management import BaseCommand
from django.db import IntegrityError
import logging
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
                'is_active': True,
                'is_merchandiser': True,
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
        # Create some locations
        ###############################################################################
        decorate_model_creation(Location)

        # Get the universal location or create it if it doesn't exist
        universal_location = Location.objects.filter(is_universal=True).first()
        if not universal_location:
            universal_location = create_shit(Location, 'At the Soonest Tournament', dict(
                name='At the Soonest Tournament',
                address='Will be specified by the tournament organizer',
                merchandiser=admin,
                is_universal=True,
                note='Items will be available for pickup at the next tournament. Please check the tournament schedule.'
            ))

        # Create locations for admin
        admin_location1 = create_shit(Location, 'Prague Office', dict(
            name='Prague Office',
            address='Václavské náměstí 1, 110 00 Praha 1',
            merchandiser=admin,
            note='Available for pickup Monday-Friday, 9:00-17:00'
        ))

        admin_location2 = create_shit(Location, 'Brno Store', dict(
            name='Brno Store',
            address='Náměstí Svobody 20, 602 00 Brno',
            merchandiser=admin,
            note='Available for pickup Monday-Saturday, 10:00-18:00'
        ))

        # Create locations for test_merchandiser
        merch_location1 = create_shit(Location, 'Ostrava Pickup Point', dict(
            name='Ostrava Pickup Point',
            address='Masarykovo náměstí 15, 702 00 Ostrava',
            merchandiser=test_merchandiser,
            note='Available for pickup on weekends only'
        ))

        merch_location2 = create_shit(Location, 'Plzeň Training Center', dict(
            name='Plzeň Training Center',
            address='Americká 42, 301 00 Plzeň',
            merchandiser=test_merchandiser,
            note='Available during training sessions'
        ))

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
        # Create parent t-shirt item
        t_shirt = create_shit(Item, 'Tričko s tučňákem', dict(
            name='Tričko s tučňákem',
            merchandiser=admin,
            amount=30,
            price=499,
            short_description='Kvalitní bavlněné tričko s potiskem tučňáka',
            is_active=True,
            description='Pohodlné bavlněné tričko s roztomilým potiskem tučňáka. Vhodné pro každodenní nošení. K dispozici ve všech velikostech.'
        ))
        t_shirt.category.add(clothes_category)
        t_shirt.locations.add(universal_location, admin_location1, admin_location2)

        # Create color variants for t-shirt
        t_shirt_red = create_shit(Item, 'Tričko s tučňákem - Červené', dict(
            name='Tričko s tučňákem',
            merchandiser=admin,
            amount=20,
            price=499,
            short_description='Kvalitní bavlněné tričko s potiskem tučňáka',
            is_active=True,
            description='Pohodlné bavlněné tričko s roztomilým potiskem tučňáka. Vhodné pro každodenní nošení. K dispozici ve všech velikostech.',
            parent_item=t_shirt,
            is_variant=True,
            color='Červená'
        ))
        t_shirt_red.category.add(clothes_category)
        t_shirt_red.locations.add(universal_location, admin_location1, admin_location2)

        t_shirt_blue = create_shit(Item, 'Tričko s tučňákem - Modré', dict(
            name='Tričko s tučňákem',
            merchandiser=admin,
            amount=18,
            price=499,
            short_description='Kvalitní bavlněné tričko s potiskem tučňáka',
            is_active=True,
            description='Pohodlné bavlněné tričko s roztomilým potiskem tučňáka. Vhodné pro každodenní nošení. K dispozici ve všech velikostech.',
            parent_item=t_shirt,
            is_variant=True,
            color='Modrá'
        ))
        t_shirt_blue.category.add(clothes_category)
        t_shirt_blue.locations.add(universal_location, admin_location1, admin_location2)

        t_shirt_green = create_shit(Item, 'Tričko s tučňákem - Zelené', dict(
            name='Tričko s tučňákem',
            merchandiser=admin,
            amount=20,
            price=499,
            short_description='Kvalitní bavlněné tričko s potiskem tučňáka',
            is_active=True,
            description='Pohodlné bavlněné tričko s roztomilým potiskem tučňáka. Vhodné pro každodenní nošení. K dispozici ve všech velikostech.',
            parent_item=t_shirt,
            is_variant=True,
            color='Zelená'
        ))
        t_shirt_green.category.add(clothes_category)
        t_shirt_green.locations.add(universal_location, admin_location1, admin_location2)

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
        long_socks.locations.add(universal_location, merch_location1, merch_location2)

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
        frisbee.locations.add(universal_location, admin_location1)

        # Create parent shorts item
        shorts = create_shit(Item, 'Sportovní šortky', dict(
            name='Sportovní šortky',
            merchandiser=test_merchandiser,
            amount=15,
            price=599,
            short_description='Lehké prodyšné šortky',
            is_active=True,
            description='Pohodlné sportovní šortky ideální pro Ultimate frisbee. Rychleschnoucí materiál.'
        ))
        shorts.category.add(clothes_category)
        shorts.locations.add(universal_location, merch_location2)

        # Create color variants for shorts
        shorts_black = create_shit(Item, 'Sportovní šortky - Černé', dict(
            name='Sportovní šortky',
            merchandiser=test_merchandiser,
            amount=10,
            price=599,
            short_description='Lehké prodyšné šortky',
            is_active=True,
            description='Pohodlné sportovní šortky ideální pro Ultimate frisbee. Rychleschnoucí materiál.',
            parent_item=shorts,
            is_variant=True,
            color='Černá'
        ))
        shorts_black.category.add(clothes_category)
        shorts_black.locations.add(universal_location, merch_location2)

        shorts_navy = create_shit(Item, 'Sportovní šortky - Námořnická', dict(
            name='Sportovní šortky',
            merchandiser=test_merchandiser,
            amount=10,
            price=599,
            short_description='Lehké prodyšné šortky',
            is_active=True,
            description='Pohodlné sportovní šortky ideální pro Ultimate frisbee. Rychleschnoucí materiál.',
            parent_item=shorts,
            is_variant=True,
            color='Námořnická'
        ))
        shorts_navy.category.add(clothes_category)
        shorts_navy.locations.add(universal_location, merch_location2)

        shorts_white = create_shit(Item, 'Sportovní šortky - Bílé', dict(
            name='Sportovní šortky',
            merchandiser=test_merchandiser,
            amount=10,
            price=599,
            short_description='Lehké prodyšné šortky',
            is_active=True,
            description='Pohodlné sportovní šortky ideální pro Ultimate frisbee. Rychleschnoucí materiál.',
            parent_item=shorts,
            is_variant=True,
            color='Bílá'
        ))
        shorts_white.category.add(clothes_category)
        shorts_white.locations.add(universal_location, merch_location2)

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
        cap.locations.add(universal_location, admin_location2)

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
        water_bottle.locations.add(universal_location, merch_location1)

        # Create parent sweatshirt item
        sweatshirt = create_shit(Item, 'Mikina UFO', dict(
            name='Mikina UFO',
            merchandiser=admin,
            amount=10,
            price=899,
            short_description='Teplá mikina s kapucí',
            is_active=True,
            description='Pohodlná mikina s kapucí a klokaní kapsou. Logo UFO na přední straně.'
        ))
        sweatshirt.category.add(clothes_category)
        sweatshirt.locations.add(universal_location, admin_location1, admin_location2)

        # Create color variants for sweatshirt
        sweatshirt_gray = create_shit(Item, 'Mikina UFO - Šedá', dict(
            name='Mikina UFO',
            merchandiser=admin,
            amount=10,
            price=899,
            short_description='Teplá mikina s kapucí',
            is_active=True,
            description='Pohodlná mikina s kapucí a klokaní kapsou. Logo UFO na přední straně.',
            parent_item=sweatshirt,
            is_variant=True,
            color='Šedá'
        ))
        sweatshirt_gray.category.add(clothes_category)
        sweatshirt_gray.locations.add(universal_location, admin_location1, admin_location2)

        sweatshirt_black = create_shit(Item, 'Mikina UFO - Černá', dict(
            name='Mikina UFO',
            merchandiser=admin,
            amount=10,
            price=899,
            short_description='Teplá mikina s kapucí',
            is_active=True,
            description='Pohodlná mikina s kapucí a klokaní kapsou. Logo UFO na přední straně.',
            parent_item=sweatshirt,
            is_variant=True,
            color='Černá'
        ))
        sweatshirt_black.category.add(clothes_category)
        sweatshirt_black.locations.add(universal_location, admin_location1, admin_location2)

        sweatshirt_purple = create_shit(Item, 'Mikina UFO - Fialová', dict(
            name='Mikina UFO',
            merchandiser=admin,
            amount=10,
            price=899,
            short_description='Teplá mikina s kapucí',
            is_active=True,
            description='Pohodlná mikina s kapucí a klokaní kapsou. Logo UFO na přední straně.',
            parent_item=sweatshirt,
            is_variant=True,
            color='Fialová'
        ))
        sweatshirt_purple.category.add(clothes_category)
        sweatshirt_purple.locations.add(universal_location, admin_location1, admin_location2)

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
        wristband.locations.add(universal_location, merch_location1, merch_location2)

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
        backpack.locations.add(universal_location, admin_location1)

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
        beanie.locations.add(universal_location, merch_location2)

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
        towel.locations.add(universal_location, admin_location2)

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
        training_shirt.locations.add(universal_location, merch_location1, merch_location2)

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
        socks.locations.add(universal_location, admin_location1, admin_location2)

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
        sleeve.locations.add(universal_location, merch_location1)

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
            item=long_socks,
            pickup_location=merch_location1
        ))
        order_item_2 = create_shit(OrderItem, 'Order item 2', dict(
            order=cart_order,
            amount=1,
            item=frisbee,
            pickup_location=admin_location1
        ))

        # Order in cart for test_user
        test_user_cart = create_shit(Order, 'Test user cart', dict(
            user=test_user,
            status=Order.Status.IN_CART
        ))
        # Use a color variant in the order
        order_item_3 = create_shit(OrderItem, 'Order item 3', dict(
            order=test_user_cart,
            item=t_shirt_red,  # Use the red variant instead of the parent
            amount=1,
            pickup_location=admin_location1
        ))
        order_item_4 = create_shit(OrderItem, 'Order item 4', dict(
            order=test_user_cart,
            item=cap,
            amount=1,
            pickup_location=universal_location
        ))

        # Ordered orders
        ordered1 = create_shit(Order, 'Order ordered 1', dict(
            user=test_user,
            status=Order.Status.ORDERED,
            contact_email=test_user.email,
            contact_phone=test_user.phone or '123456789'
        ))
        order_item_5 = create_shit(OrderItem, 'Order item 5', dict(
            order=ordered1,
            item=backpack,
            amount=1,
            pickup_location=admin_location1
        ))
        order_item_6 = create_shit(OrderItem, 'Order item 6', dict(
            order=ordered1,
            item=water_bottle,
            amount=2,
            pickup_location=merch_location1
        ))

        ordered2 = create_shit(Order, 'Order ordered 2', dict(
            user=test_merchandiser,
            status=Order.Status.ORDERED,
            contact_email=test_merchandiser.email,
            contact_phone=test_merchandiser.phone or '987654321'
        ))
        # Use a color variant in the order
        order_item_7 = create_shit(OrderItem, 'Order item 7', dict(
            order=ordered2,
            item=sweatshirt_black,  # Use the black variant instead of the parent
            amount=1,
            pickup_location=universal_location
        ))

        # Fulfilled orders
        fulfilled1 = create_shit(Order, 'Order fulfilled 1', dict(
            user=admin,
            status=Order.Status.FULFILLED,
            contact_email=admin.email,
            contact_phone=admin.phone or '555123456'
        ))
        order_item_8 = create_shit(OrderItem, 'Order item 8', dict(
            order=fulfilled1,
            item=t_shirt,
            amount=3,
            pickup_location=admin_location2
        ))
        order_item_9 = create_shit(OrderItem, 'Order item 9', dict(
            order=fulfilled1,
            item=long_socks,
            amount=2,
            pickup_location=universal_location
        ))

        fulfilled2 = create_shit(Order, 'Order fulfilled 2', dict(
            user=test_user,
            status=Order.Status.FULFILLED,
            contact_email=test_user.email,
            contact_phone=test_user.phone or '555987654'
        ))
        order_item_10 = create_shit(OrderItem, 'Order item 10', dict(
            order=fulfilled2,
            item=sleeve,
            amount=2,
            pickup_location=merch_location1
        ))
        order_item_11 = create_shit(OrderItem, 'Order item 11', dict(
            order=fulfilled2,
            item=towel,
            amount=1,
            pickup_location=admin_location2
        ))
        # Add a new order item with shorts variant
        order_item_12 = create_shit(OrderItem, 'Order item 12', dict(
            order=fulfilled2,
            item=shorts_navy,  # Use the navy shorts variant
            amount=1,
            pickup_location=merch_location2
        ))

        ###############################################################################
        # Create some News
        ###############################################################################
        decorate_model_creation(News)

        news1 = create_shit(News, 'New Tournament Announced', dict(
            title='New Tournament Announced',
            content='We are excited to announce our upcoming summer tournament! Join us for a weekend of fun, competition, and community. Registration opens next week.',
            is_active=True
        ))

        news2 = create_shit(News, 'New Merchandise Available', dict(
            title='New Merchandise Available',
            content='Check out our latest merchandise collection! We have added new t-shirts, discs, and accessories to our shop. Limited quantities available, so get yours before they\'re gone!',
            is_active=True
        ))

        news3 = create_shit(News, 'Training Camp Registration', dict(
            title='Training Camp Registration',
            content='Registration for our annual training camp is now open! This year\'s camp will focus on advanced throwing techniques and strategic gameplay. Perfect for players of all levels.',
            is_active=True
        ))

        news4 = create_shit(News, 'Community Cleanup Event', dict(
            title='Community Cleanup Event',
            content='Join us this Saturday for our community cleanup event at the local park. Let\'s give back to the community that supports our sport! Refreshments will be provided.',
            is_active=True
        ))

        news5 = create_shit(News, 'Team Tryouts', dict(
            title='Team Tryouts',
            content='Tryouts for the competitive team will be held next month. We\'re looking for dedicated players who want to represent our club at national tournaments. See the details on our website.',
            is_active=True
        ))
