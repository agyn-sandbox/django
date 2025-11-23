from django.core import checks
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Command that fails system checks unless skipped.'

    def _run_checks(self, **kwargs):
        return [
            checks.Error(
                'System check failure for syscheck_command.',
                id='admin_scripts.E001',
            )
        ]

    def handle(self, *args, **options):
        print('EXECUTE:SysCheckCommand options=%s' % (sorted(options.items()),))
