from django.core.management.base import BaseCommand


class Command(BaseCommand):

    def add_arguments(self, parser):
        primary_group = parser.add_mutually_exclusive_group(required=True)
        primary_group.add_argument('--primary-id', type=int, dest='primary_id')
        primary_group.add_argument('--primary-name', dest='primary_name')

        secondary_group = parser.add_mutually_exclusive_group(required=True)
        secondary_group.add_argument('--region-id', type=int, dest='region_id')
        secondary_group.add_argument('--region-name', dest='region_name')

    def handle(self, *args, **options):
        self.stdout.write('primary_id=%s' % options.get('primary_id'))
        self.stdout.write('primary_name=%s' % options.get('primary_name'))
        self.stdout.write('region_id=%s' % options.get('region_id'))
        self.stdout.write('region_name=%s' % options.get('region_name'))
