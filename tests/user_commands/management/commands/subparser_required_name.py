from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Command with subparser requiring a positional argument."

    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(dest="action", required=True)
        create_parser = subparsers.add_parser("create")
        create_parser.add_argument("name")

    def handle(self, *args, **options):
        return None
