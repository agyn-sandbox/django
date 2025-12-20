from django.core.management.base import BaseCommand


class Command(BaseCommand):

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=False)
        group.add_argument('--optional-alpha', dest='optional_alpha')
        group.add_argument('--optional-beta', dest='optional_beta')

    def handle(self, *args, **options):
        self.stdout.write('optional_alpha=%s' % options.get('optional_alpha'))
        self.stdout.write('optional_beta=%s' % options.get('optional_beta'))
