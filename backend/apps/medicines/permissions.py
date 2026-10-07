from rest_framework.permissions import BasePermission, SAFE_METHODS


class CatalogPermission(BasePermission):
    """Allow authenticated reads and restrict catalogue mutations to staff roles."""

    write_roles = {
        "pharmacy_owner",
        "pharmacy_manager",
        "pharmacist",
        "inventory_manager",
    }

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return user.is_superuser or user.has_role(*self.write_roles)
