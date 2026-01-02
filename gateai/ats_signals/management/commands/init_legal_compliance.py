from django.core.management.base import BaseCommand
from ats_signals.legal_disclaimers import create_default_disclaimers, create_default_retention_policies

class Command(BaseCommand):
    help = 'Initialize legal compliance data including disclaimers and retention policies'

    def handle(self, *args, **options):
        self.stdout.write('Creating default legal disclaimers...')
        create_default_disclaimers()
        self.stdout.write(self.style.SUCCESS('Legal disclaimers created successfully'))
        
        self.stdout.write('Creating default data retention policies...')
        create_default_retention_policies()
        self.stdout.write(self.style.SUCCESS('Data retention policies created successfully'))
        
        self.stdout.write(self.style.SUCCESS('Legal compliance initialization completed')) 