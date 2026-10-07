"""Role-based access control (RBAC) permission classes."""
from rest_framework.permissions import BasePermission


class IsSuperAdmin(BasePermission):
    message = "Super admin access required."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_superuser)


class IsInRole(BasePermission):
    """Allow access when the user's role code is in ``allowed_roles``."""

    allowed_roles: set = set()
    message = "You do not have permission to perform this action."

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if user.is_superuser:
            return True
        return bool(user.role and user.role.code in self.allowed_roles)


class IsPharmacyOwner(IsInRole):
    allowed_roles = {"pharmacy_owner"}


class IsPharmacyManager(IsInRole):
    allowed_roles = {"pharmacy_manager"}


class IsAccountant(IsInRole):
    allowed_roles = {"accountant"}


class IsPharmacist(IsInRole):
    allowed_roles = {"pharmacist"}


class IsInventoryManager(IsInRole):
    allowed_roles = {"inventory_manager"}


class IsCashier(IsInRole):
    allowed_roles = {"cashier"}


class IsStaffRole(IsInRole):
    allowed_roles = {
        "pharmacy_owner",
        "pharmacy_manager",
        "accountant",
        "pharmacist",
        "inventory_manager",
        "cashier",
    }
