from django.core.management.base import BaseCommand


class Command(BaseCommand):

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--shop-id', type=int, dest='shop_id')
        group.add_argument('--shop-name', dest='shop_name')

    def handle(self, *args, **options):
        shop_id = options.get('shop_id')
        shop_name = options.get('shop_name')
        self.stdout.write('shop_id=%s' % shop_id)
        self.stdout.write('shop_name=%s' % shop_name)
