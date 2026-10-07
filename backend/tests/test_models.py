from datetime import date

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.core.exceptions import ValidationError

from apps.accounts.models import Permission, Role, UserBranch
from apps.branches.models import Branch, Warehouse
from apps.pharmacies.models import Pharmacy

User = get_user_model()


class RoleAndPermissionTests(TestCase):
    def test_role_code_is_unique(self):
        Role.objects.create(name="Cashier I", code="cashier")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Role.objects.create(name="Cashier II", code="cashier")

    def test_permission_code_is_unique(self):
        Permission.objects.create(code="sales.create", name="Create sales", module="sales")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Permission.objects.create(
                    code="sales.create", name="Duplicate", module="sales"
                )

    def test_user_has_role_helper(self):
        role = Role.objects.create(name="Accountant", code="accountant")
        user = User.objects.create_user(
            username="acc1", email="acc1@pharmafin.test", password="x", role=role
        )
        self.assertTrue(user.has_role("accountant"))
        self.assertFalse(user.has_role("cashier"))
        self.assertEqual(user.role_code, "accountant")

    def test_superuser_passes_every_role_check(self):
        admin = User.objects.create_superuser(
            username="root", email="root@pharmafin.test", password="x"
        )
        self.assertTrue(admin.has_role("anything"))


class PharmacyAndBranchTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner1", email="owner1@pharmafin.test", password="x"
        )
        self.pharmacy = Pharmacy.objects.create(
            owner=self.owner,
            name="City Care Pharmacy",
            country="PK",
            city="Lahore",
            currency="PKR",
        )

    def test_pharmacy_default_status_is_active(self):
        self.assertEqual(self.pharmacy.status, "active")

    def test_pharmacy_requires_country(self):
        with self.assertRaises(ValidationError):
            bad = Pharmacy(owner=self.owner, name="No Country")
            bad.full_clean()

    def test_branch_code_unique_per_pharmacy(self):
        Branch.objects.create(pharmacy=self.pharmacy, name="Main", code="main")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Branch.objects.create(pharmacy=self.pharmacy, name="Other", code="main")

    def test_same_branch_code_allowed_on_different_pharmacy(self):
        Branch.objects.create(pharmacy=self.pharmacy, name="Main", code="main")
        other = Pharmacy.objects.create(
            owner=self.owner, name="Rival Pharmacy", country="PK"
        )
        Branch.objects.create(pharmacy=other, name="Main", code="main")  # no clash

    def test_warehouse_unique_code_per_branch(self):
        branch = Branch.objects.create(pharmacy=self.pharmacy, name="Main", code="main")
        Warehouse.objects.create(branch=branch, name="Back store", code="back")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Warehouse.objects.create(branch=branch, name="Other", code="back")

    def test_user_branch_assignment_unique(self):
        branch = Branch.objects.create(pharmacy=self.pharmacy, name="Main", code="main")
        UserBranch.objects.create(user=self.owner, branch=branch, is_default=True)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                UserBranch.objects.create(user=self.owner, branch=branch)


class MigrationIntegrityTests(TestCase):
    """Sanity checks that money/DB columns are exact (Decimal) not float."""

    def test_price_columns_are_decimal(self):
        from apps.medicines.models import MedicineBatch

        for field_name in ("purchase_price", "selling_price"):
            field = MedicineBatch._meta.get_field(field_name)
            self.assertEqual(field.__class__.__name__, "DecimalField")
            self.assertEqual(field.max_digits, 12)
            self.assertEqual(field.decimal_places, 2)

    def test_expiry_date_is_indexed(self):
        from apps.medicines.models import MedicineBatch

        field = MedicineBatch._meta.get_field("expiry_date")
        self.assertTrue(field.db_index)

    def test_batch_ordering_is_fefo_friendly(self):
        from apps.medicines.models import MedicineBatch

        self.assertEqual(MedicineBatch._meta.ordering, ["expiry_date"])
