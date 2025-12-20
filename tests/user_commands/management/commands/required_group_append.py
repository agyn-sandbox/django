from django.core.management.base import BaseCommand


class Command(BaseCommand):

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--tag', action='append', nargs=2, dest='tags')
        group.add_argument('--label', dest='label')

    def handle(self, *args, **options):
        tags = options.get('tags')
        if tags is None:
            self.stdout.write('tags=None')
        else:
            formatted = '|'.join(' '.join(values) for values in tags)
            self.stdout.write('tags=%s' % formatted)
        self.stdout.write('label=%s' % options.get('label'))
