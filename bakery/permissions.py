from django.contrib.auth.mixins import UserPassesTestMixin

from .services import ROLE_ADMIN, ROLE_CASHIER, ROLE_INVENTORY


def user_has_role(user, *roles):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=roles).exists()


class RoleRequiredMixin(UserPassesTestMixin):
    allowed_roles = ()

    def test_func(self):
        return user_has_role(self.request.user, *self.allowed_roles)
