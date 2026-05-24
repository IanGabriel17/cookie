from django.core.management.base import BaseCommand

from bakery.services import bootstrap_default_categories, bootstrap_roles


class Command(BaseCommand):
    help = "Creates role groups and starter product categories for the bakery system."

    def handle(self, *args, **options):
        bootstrap_roles()
        bootstrap_default_categories()

        self.stdout.write(self.style.SUCCESS("Role groups and starter categories created."))
