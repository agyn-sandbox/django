from django.core.management.base import BaseCommand


class Command(BaseCommand):

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--enable-shop', action='store_true', dest='shop_enabled')
        group.add_argument('--disable-shop', action='store_false', dest='shop_enabled')

    def handle(self, *args, **options):
        self.stdout.write('shop_enabled=%s' % options['shop_enabled'])
