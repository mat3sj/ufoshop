from django.core.management import BaseCommand
from django.db import IntegrityError
import logging

from ufo_shop.models import *

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = f'Create some data in order to play with during the developement'

    def handle(self, *args, **options):
        # Create categories
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
                supplier=User.objects.get(pk=1),
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
                supplier=User.objects.get(pk=1),
                amount=88,
                short_description='Pohodlné a odolné nákolenky pro Ultimate frisbee',
                is_active=True,
                description='Kvalitní nákolenky speciálně navržené pro Ultimate frisbee. Chrání kolena při skluzech a pádech. Elastický materiál zajišťuje pohodlné nošení. Dostupné ve velikostech S-XL.'
            )
            pads.category.add(Category.objects.get(name='Náčiní'))
            logger.info('Item %s was created', 'Fešácký nákolenky')
