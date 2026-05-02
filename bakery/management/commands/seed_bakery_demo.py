from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand

from bakery.services import ROLE_CASHIER, ROLE_INVENTORY, bootstrap_roles


class Command(BaseCommand):
    help = "Creates role groups and default demo accounts for the bakery system."

    def handle(self, *args, **options):
        bootstrap_roles()

        admin_user, created = User.objects.get_or_create(username="admin")
        if created:
            admin_user.set_password("admin1234")
            admin_user.is_superuser = True
            admin_user.is_staff = True
            admin_user.save()

        cashier, created = User.objects.get_or_create(username="cashier")
        if created:
            cashier.set_password("cashier1234")
            cashier.is_staff = True
            cashier.save()
            cashier.groups.add(Group.objects.get(name=ROLE_CASHIER))

        inventory, created = User.objects.get_or_create(username="inventory")
        if created:
            inventory.set_password("inventory1234")
            inventory.is_staff = True
            inventory.save()
            inventory.groups.add(Group.objects.get(name=ROLE_INVENTORY))

        self.stdout.write(self.style.SUCCESS("Role groups and default accounts created."))
