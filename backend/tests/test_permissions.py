from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.accounts.models import Role
from common.permissions import (
    IsAccountant,
    IsCashier,
    IsInRole,
    IsPharmacist,
    IsStaffRole,
    IsSuperAdmin,
)

User = get_user_model()


class RbacPermissionTests(TestCase):
    """Role-based permission classes must enforce role codes correctly."""

    @classmethod
    def setUpTestData(cls):
        cls.pharmacist = User.objects.create_user(
            username="p1",
            email="p1@pharmafin.test",
            password="x",
            role=Role.objects.create(name="Pharmacist", code="pharmacist"),
        )
        cls.cashier = User.objects.create_user(
            username="c1",
            email="c1@pharmafin.test",
            password="x",
            role=Role.objects.create(name="Cashier", code="cashier"),
        )
        cls.admin = User.objects.create_superuser(
            username="root2", email="root2@pharmafin.test", password="x"
        )
        cls.anonymous = SimpleNamespace(user=SimpleNamespace(is_authenticated=False))

    def _request(self, user):
        return SimpleNamespace(user=user)

    def test_pharmacist_passes_pharmacist_permission(self):
        perm = IsPharmacist()
        self.assertTrue(perm.has_permission(self._request(self.pharmacist), None))

    def test_cashier_fails_pharmacist_permission(self):
        perm = IsPharmacist()
        self.assertFalse(perm.has_permission(self._request(self.cashier), None))

    def test_superadmin_bypasses_role_checks(self):
        self.assertTrue(IsCashier().has_permission(self._request(self.admin), None))
        self.assertTrue(IsAccountant().has_permission(self._request(self.admin), None))
        self.assertTrue(IsInRole().has_permission(self._request(self.admin), None))

    def test_staff_role_includes_pharmacist_but_not_customer(self):
        customer = User.objects.create_user(
            username="cu1",
            email="cu1@pharmafin.test",
            password="x",
            role=Role.objects.create(name="Customer", code="customer"),
        )
        self.assertTrue(IsStaffRole().has_permission(self._request(self.pharmacist), None))
        self.assertFalse(IsStaffRole().has_permission(self._request(customer), None))

    def test_unauthenticated_denied(self):
        self.assertFalse(IsSuperAdmin().has_permission(self.anonymous, None))
        self.assertFalse(IsInRole().has_permission(self.anonymous, None))
