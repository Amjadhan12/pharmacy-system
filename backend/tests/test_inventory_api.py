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
from apps.transactions.services import (
    fifo_batches,
    record_stock_movement,
)


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

    def test_batch_create_records_opening_stock_in_ledger(self):
        client = APIClient()
        client.force_authenticate(user=self.user)

        response = client.post(
            "/api/v1/medicines/batches/",
            {
                "medicine": self.medicine.pk,
                "branch": self.branch.pk,
                "warehouse": self.warehouse.pk,
                "batch_number": "API-CREATE",
                "purchase_price": "12.75",
                "selling_price": "18.50",
                "quantity": 9,
                "expiry_date": (date.today() + timedelta(days=180)).isoformat(),
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201, response.content)
        batch = MedicineBatch.objects.get(batch_number="API-CREATE")
        movement = InventoryTransaction.objects.get(batch=batch)
        self.assertEqual(batch.quantity, 9)
        self.assertEqual(movement.transaction_type, "receipt")
        self.assertEqual(movement.direction, "in")
        self.assertEqual(movement.quantity, 9)
        self.assertEqual(str(batch.purchase_price), "12.75")

    def test_inventory_expiry_low_stock_and_fefo_endpoints(self):
        expired = self.make_batch("API-EXPIRED", -1, 3)
        soon = self.make_batch("API-SOON", 10, 4)
        later = self.make_batch("API-LATER", 80, 6)
        self.medicine.reorder_level = 11
        self.medicine.save(update_fields=["reorder_level"])
        client = APIClient()
        client.force_authenticate(user=self.user)

        expired_response = client.get("/api/v1/inventory/expired/")
        expiring_response = client.get(
            "/api/v1/inventory/expiring/?days=30"
        )
        low_stock_response = client.get("/api/v1/inventory/low-stock/")
        fefo_response = client.get(
            f"/api/v1/inventory/fefo/{self.medicine.pk}/"
            f"?branch={self.branch.pk}&quantity=5"
        )

        self.assertEqual(expired_response.status_code, 200)
        self.assertEqual(
            [row["id"] for row in expired_response.json()["data"]["results"]],
            [expired.pk],
        )
        self.assertEqual(expiring_response.status_code, 200)
        self.assertEqual(
            [row["id"] for row in expiring_response.json()["data"]["results"]],
            [soon.pk],
        )
        self.assertEqual(low_stock_response.status_code, 200)
        self.assertEqual(
            [row["id"] for row in low_stock_response.json()["data"]["results"]],
            [self.medicine.pk],
        )
        self.assertEqual(fefo_response.status_code, 200, fefo_response.content)
        allocations = fefo_response.json()["data"]["allocations"]
        self.assertEqual(
            [(row["batch"]["id"], row["quantity"]) for row in allocations],
            [(soon.pk, 4), (later.pk, 1)],
        )

    def test_transfer_creates_paired_ledger_rows_and_moves_stock(self):
        source = self.make_batch("TRANSFER-SOURCE", 60, 10)
        destination = self.make_batch("TRANSFER-DESTINATION", 120, 2)
        client = APIClient()
        client.force_authenticate(user=self.user)

        response = client.post(
            "/api/v1/inventory/transfers/",
            {
                "source_batch": source.pk,
                "destination_batch": destination.pk,
                "quantity": 4,
                "reference": "MOVE-001",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201, response.content)
        source.refresh_from_db()
        destination.refresh_from_db()
        self.assertEqual((source.quantity, destination.quantity), (6, 6))
        rows = InventoryTransaction.objects.filter(reference__startswith="MOVE-001")
        self.assertEqual(rows.count(), 2)
        self.assertEqual(set(rows.values_list("direction", flat=True)), {"in", "out"})
