from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import Role, UserBranch
from apps.accounting.models import LedgerAccount
from apps.branches.models import Branch, Warehouse
from apps.customers.models import Customer
from apps.medicines.models import (
    DosageForm,
    Medicine,
    MedicineBatch,
    MedicineCategory,
)
from apps.pharmacies.models import Pharmacy
from apps.suppliers.models import Supplier

User = get_user_model()


class TenantApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        role = Role.objects.create(name="Pharmacist", code="pharmacist")
        cls.user = User.objects.create_user(
            username="tenant-pharmacist",
            email="tenant-pharmacist@pharmafin.test",
            password="Tenant-Pass-123",
            role=role,
        )
        owner_role = Role.objects.create(name="Pharmacy Owner", code="pharmacy_owner")
        other_owner = User.objects.create_user(
            username="other-owner",
            email="other-owner@pharmafin.test",
            password="Tenant-Pass-123",
            role=owner_role,
        )
        cls.pharmacy = Pharmacy.objects.create(
            owner=other_owner, name="Assigned Pharmacy", country="AF"
        )
        other_pharmacy = Pharmacy.objects.create(
            owner=other_owner, name="Unassigned Pharmacy", country="AF"
        )
        cls.branch = Branch.objects.create(
            pharmacy=cls.pharmacy, name="Assigned Branch", code="assigned"
        )
        other_branch = Branch.objects.create(
            pharmacy=other_pharmacy, name="Unassigned Branch", code="unassigned"
        )
        UserBranch.objects.create(user=cls.user, branch=cls.branch, is_default=True)
        cls.warehouse = Warehouse.objects.create(
            branch=cls.branch, name="Assigned Warehouse", code="assigned"
        )
        other_warehouse = Warehouse.objects.create(
            branch=other_branch, name="Unassigned Warehouse", code="unassigned"
        )
        category = MedicineCategory.objects.create(
            name="Tenant Test Category", code="tenant-test-category"
        )
        dosage_form = DosageForm.objects.create(
            name="Tenant Test Tablet", code="tenant-test-tablet"
        )
        cls.medicine = Medicine.objects.create(
            generic_name="Tenant Test Medicine",
            category=category,
            dosage_form=dosage_form,
            reorder_level=20,
        )
        cls.batch = MedicineBatch.objects.create(
            medicine=cls.medicine,
            branch=cls.branch,
            warehouse=cls.warehouse,
            batch_number="TENANT-A",
            quantity=12,
            expiry_date=date.today() + timedelta(days=20),
        )
        cls.other_batch = MedicineBatch.objects.create(
            medicine=cls.medicine,
            branch=other_branch,
            warehouse=other_warehouse,
            batch_number="TENANT-B",
            quantity=80,
            expiry_date=date.today() + timedelta(days=200),
        )
        cls.supplier = Supplier.objects.create(
            pharmacy=cls.pharmacy, name="Assigned Supplier"
        )
        Supplier.objects.create(pharmacy=other_pharmacy, name="Other Supplier")
        cls.customer = Customer.objects.create(
            pharmacy=cls.pharmacy,
            first_name="Assigned",
            last_name="Customer",
            email="assigned-customer@pharmafin.test",
        )
        Customer.objects.create(
            pharmacy=other_pharmacy,
            first_name="Other",
            last_name="Customer",
            email="other-customer@pharmafin.test",
        )
        cls.account = LedgerAccount.objects.create(
            account_code="TA-1000",
            name="Assigned Cash",
            account_type="asset",
            currency="AFN",
            pharmacy=cls.pharmacy,
        )
        cls.other_account = LedgerAccount.objects.create(
            account_code="TB-1000",
            name="Other Cash",
            account_type="asset",
            currency="AFN",
            pharmacy=other_pharmacy,
        )

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def get_results(self, path):
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200, response.content)
        return response.json()["data"]["results"]

    def test_user_profile_includes_only_accessible_tenant_context(self):
        response = self.client.get("/api/v1/auth/me/")

        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual([item["id"] for item in data["pharmacies"]], [self.pharmacy.id])
        self.assertEqual([item["id"] for item in data["branches"]], [self.branch.id])
        self.assertEqual(data["role"]["code"], "pharmacist")

    def test_tenant_lists_only_include_owned_or_assigned_records(self):
        expected = {
            "/api/v1/pharmacies/": self.pharmacy.id,
            "/api/v1/branches/": self.branch.id,
            "/api/v1/branches/warehouses/": self.warehouse.id,
            "/api/v1/medicines/batches/": self.batch.id,
            "/api/v1/suppliers/": self.supplier.id,
            "/api/v1/customers/": self.customer.id,
            "/api/v1/accounting/accounts/": self.account.id,
        }

        for path, allowed_id in expected.items():
            with self.subTest(path=path):
                results = self.get_results(path)
                self.assertEqual([row["id"] for row in results], [allowed_id])

    def test_cross_tenant_branch_inventory_and_account_are_not_visible(self):
        for path in (
            f"/api/v1/branches/{self.other_batch.branch_id}/",
            f"/api/v1/medicines/batches/{self.other_batch.id}/",
        ):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 404)

        accounts = self.get_results(
            f"/api/v1/accounting/accounts/?pharmacy={self.other_account.pharmacy_id}"
        )
        self.assertEqual(accounts, [])

    def test_dashboard_summary_uses_accessible_database_records(self):
        response = self.client.get("/api/v1/dashboard/summary/")

        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["pharmacies"], 1)
        self.assertEqual(data["branches"], 1)
        self.assertEqual(data["medicines"], 1)
        self.assertEqual(data["active_medicines"], 1)
        self.assertEqual(data["low_stock_medicines"], 1)
        self.assertEqual(data["batches"], 1)
        self.assertEqual(data["stock_units"], 12)
        self.assertEqual(data["expiring_batches"], 1)
        self.assertEqual(data["suppliers"], 1)
        self.assertEqual(data["customers"], 1)

    def test_unassigned_user_cannot_list_other_tenant_data(self):
        unassigned = User.objects.create_user(
            username="no-tenant",
            email="no-tenant@pharmafin.test",
            password="Tenant-Pass-123",
        )
        self.client.force_authenticate(user=unassigned)

        for path in (
            "/api/v1/pharmacies/",
            "/api/v1/branches/",
            "/api/v1/branches/warehouses/",
            "/api/v1/medicines/batches/",
            "/api/v1/suppliers/",
            "/api/v1/customers/",
            "/api/v1/accounting/accounts/",
        ):
            with self.subTest(path=path):
                self.assertEqual(self.get_results(path), [])

    def test_catalog_search_and_supplier_customer_crud(self):
        medicines = self.get_results(
            "/api/v1/medicines/medicines/?search=Tenant%20Test"
        )
        self.assertEqual([row["id"] for row in medicines], [self.medicine.id])

        owner_client = APIClient()
        owner_client.force_authenticate(user=self.pharmacy.owner)
        supplier_response = owner_client.post(
            "/api/v1/suppliers/",
            {
                "pharmacy": self.pharmacy.id,
                "name": "New Tenant Supplier",
                "currency": "AFN",
            },
            format="json",
        )
        self.assertEqual(supplier_response.status_code, 201, supplier_response.content)
        supplier_id = supplier_response.json()["data"]["id"]
        update_response = owner_client.patch(
            f"/api/v1/suppliers/{supplier_id}/",
            {"phone": "+93 700 999 999"},
            format="json",
        )
        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(update_response.json()["data"]["phone"], "+93 700 999 999")
        self.assertEqual(
            owner_client.delete(f"/api/v1/suppliers/{supplier_id}/").status_code,
            204,
        )

        customer_response = owner_client.post(
            "/api/v1/customers/",
            {
                "pharmacy": self.pharmacy.id,
                "first_name": "New",
                "last_name": "Tenant Customer",
                "email": "new-customer@pharmafin.test",
            },
            format="json",
        )
        self.assertEqual(customer_response.status_code, 201, customer_response.content)
        customer_id = customer_response.json()["data"]["id"]
        update_response = owner_client.patch(
            f"/api/v1/customers/{customer_id}/",
            {"phone": "+93 700 888 888"},
            format="json",
        )
        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(update_response.json()["data"]["phone"], "+93 700 888 888")

    def test_users_cannot_create_or_update_other_pharmacy_records(self):
        response = self.client.post(
            "/api/v1/suppliers/",
            {
                "pharmacy": self.other_account.pharmacy_id,
                "name": "Cross-tenant Supplier",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 403)

        response = self.client.patch(
            f"/api/v1/customers/{self.customer.id}/",
            {"pharmacy": self.other_account.pharmacy_id},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
