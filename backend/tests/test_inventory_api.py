from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import Role, UserBranch
from apps.accounts.models import User
from apps.branches.models import Branch, Warehouse
from apps.medicines.models import (
    DosageForm,
    Medicine,
    MedicineBatch,
    MedicineCategory,
)
from apps.pharmacies.models import Pharmacy
from apps.transactions.models import InventoryTransaction
from apps.transactions.services import fifo_batches, record_stock_movement


class InventoryMovementTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        role = Role.objects.create(name="Inventory Manager", code="inventory_manager")
        cls.user = User.objects.create_user(
            username="inventory-user",
            email="inventory-user@pharmafin.test",
            password="Inventory-Pass-123",
            role=role,
        )
        cls.pharmacy = Pharmacy.objects.create(
            owner=cls.user, name="Inventory Test Pharmacy", country="AF"
        )
        cls.branch = Branch.objects.create(
            pharmacy=cls.pharmacy, name="Main Branch", code="main"
        )
        cls.warehouse = Warehouse.objects.create(
            branch=cls.branch, name="Main Warehouse", code="main"
        )
        UserBranch.objects.create(user=cls.user, branch=cls.branch, is_default=True)
        category = MedicineCategory.objects.create(
            name="Inventory Test Category", code="inventory-test"
        )
        form = DosageForm.objects.create(name="Inventory Test Form", code="inventory-test")
        cls.medicine = Medicine.objects.create(
            generic_name="Inventory Test Medicine",
            category=category,
            dosage_form=form,
        )

    def make_batch(self, batch_number, expiry_offset, quantity):
        return MedicineBatch.objects.create(
            medicine=self.medicine,
            branch=self.branch,
            warehouse=self.warehouse,
            batch_number=batch_number,
            quantity=quantity,
            purchase_price="2.00",
            selling_price="4.00",
            expiry_date=date.today() + timedelta(days=expiry_offset),
            status="available",
        )

    def test_fefo_allocations_skip_expired_and_zero_quantity_batches(self):
        self.make_batch("EXPIRED", -1, 20)
        soon = self.make_batch("SOON", 5, 4)
        later = self.make_batch("LATER", 30, 8)
        self.make_batch("EMPTY", 10, 0)

        allocations, remaining = fifo_batches(self.medicine, self.branch, 6)

        self.assertEqual(
            [(row["batch"].pk, row["quantity"]) for row in allocations],
            [(soon.pk, 4), (later.pk, 2)],
        )
        self.assertEqual(remaining, 0)

    def test_dispatch_records_outgoing_movement_and_decrements_stock(self):
        batch = self.make_batch("DISPATCH", 30, 8)

        movement = record_stock_movement(
            "dispatch",
            batch,
            self.branch,
            self.warehouse,
            quantity=3,
            created_by=self.user,
        )

        batch.refresh_from_db()
        self.assertEqual(batch.quantity, 5)
        self.assertEqual(movement.direction, "out")
        self.assertEqual(movement.quantity, 3)

    def test_dispatch_rejects_expired_stock(self):
        batch = self.make_batch("EXPIRED-DISPATCH", -2, 8)

        with self.assertRaisesMessage(
            ValidationError, "Expired or unavailable batches cannot be dispatched."
        ):
            record_stock_movement(
                "dispatch", batch, self.branch, quantity=1, created_by=self.user
            )

        batch.refresh_from_db()
        self.assertEqual(batch.quantity, 8)
        self.assertFalse(
            InventoryTransaction.objects.filter(batch=batch).exists()
        )

    def test_stock_movement_endpoint_records_receipt(self):
        batch = self.make_batch("API-RECEIPT", 45, 7)
        client = APIClient()
        client.force_authenticate(user=self.user)

        response = client.post(
            "/api/v1/transactions/stock/receipt/",
            {
                "batch": batch.pk,
                "warehouse": self.warehouse.pk,
                "quantity": 5,
                "reference": "RECEIPT-API",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201, response.content)
        batch.refresh_from_db()
        self.assertEqual(batch.quantity, 12)
        self.assertEqual(response.json()["data"]["direction"], "in")

    def test_stock_movement_endpoint_denies_unassigned_user(self):
        batch = self.make_batch("DENIED", 45, 7)
        other = User.objects.create_user(
            username="unassigned",
            email="unassigned@pharmafin.test",
            password="Inventory-Pass-123",
            role=self.user.role,
        )
        client = APIClient()
        client.force_authenticate(user=other)

        response = client.post(
            "/api/v1/transactions/stock/dispatch/",
            {"batch": batch.pk, "quantity": 1},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        batch.refresh_from_db()
        self.assertEqual(batch.quantity, 7)
