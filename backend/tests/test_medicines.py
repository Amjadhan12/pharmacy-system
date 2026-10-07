from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.branches.models import Branch
from apps.medicines.models import (
    DosageForm,
    Manufacturer,
    Medicine,
    MedicineBatch,
    MedicineCategory,
)
from apps.pharmacies.models import Pharmacy

User = get_user_model()


class MedicineCatalogTests(TestCase):
    def setUp(self):
        self.category = MedicineCategory.objects.create(
            name="Analgesics", code="analgesics"
        )
        self.form = DosageForm.objects.create(name="Tablet", code="tablet")
        self.medicine = Medicine.objects.create(
            generic_name="Paracetamol",
            brand_name="Panadol",
            category=self.category,
            dosage_form=self.form,
            strength="500 mg",
            prescription_required=False,
        )

    def test_medicine_string_representation(self):
        self.assertEqual(str(self.medicine), "Panadol 500 mg")

    def test_barcode_is_unique(self):
        Medicine.objects.filter(pk=self.medicine.pk).update(barcode="BC-001")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Medicine.objects.create(
                    generic_name="Ibuprofen",
                    category=self.category,
                    dosage_form=self.form,
                    barcode="BC-001",
                )

    def test_gtin_is_unique(self):
        Medicine.objects.filter(pk=self.medicine.pk).update(gtin="1234567890123")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Medicine.objects.create(
                    generic_name="Aspirin",
                    category=self.category,
                    dosage_form=self.form,
                    gtin="1234567890123",
                )

    def test_manufacturer_optional_link(self):
        maker = Manufacturer.objects.create(name="GSK")
        medicine = Medicine.objects.create(
            generic_name="Augmentin",
            category=self.category,
            dosage_form=self.form,
            manufacturer=maker,
        )
        self.assertEqual(medicine.manufacturer.name, "GSK")


class MedicineBatchTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner2", email="owner2@pharmafin.test", password="x"
        )
        self.pharmacy = Pharmacy.objects.create(
            owner=self.owner, name="Batch Test Pharmacy", country="PK"
        )
        self.branch = Branch.objects.create(
            pharmacy=self.pharmacy, name="Main", code="main"
        )
        self.category = MedicineCategory.objects.create(
            name="Antibiotics", code="antibiotics"
        )
        self.form = DosageForm.objects.create(name="Capsule", code="capsule")
        self.medicine = Medicine.objects.create(
            generic_name="Amoxicillin",
            category=self.category,
            dosage_form=self.form,
            strength="500 mg",
        )

    def _batch(self, **overrides):
        defaults = {
            "medicine": self.medicine,
            "branch": self.branch,
            "batch_number": "B-100",
            "purchase_price": 80,
            "selling_price": 120,
            "quantity": 50,
            "expiry_date": date.today() + timedelta(days=365),
        }
        defaults.update(overrides)
        return MedicineBatch(**defaults)

    def test_batch_defaults_to_available(self):
        batch = self._batch()
        batch.full_clean()
        batch.save()
        self.assertEqual(batch.status, "available")
        self.assertFalse(batch.is_expired)

    def test_negative_purchase_price_rejected(self):
        batch = self._batch(purchase_price=-1)
        with self.assertRaises(ValidationError):
            batch.full_clean()

    def test_manufacture_after_expiry_rejected(self):
        batch = self._batch(
            manufacture_date=date.today() + timedelta(days=400),
            expiry_date=date.today() + timedelta(days=30),
        )
        with self.assertRaises(ValidationError):
            batch.full_clean()

    def test_duplicate_batch_number_same_branch_rejected(self):
        self._batch().save()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self._batch().save()

    def test_is_expired_property(self):
        batch = self._batch(expiry_date=date.today() - timedelta(days=1))
        batch.full_clean()
        self.assertTrue(batch.is_expired)

    def test_fefo_ordering_returns_earliest_expiry_first(self):
        soon = self._batch(batch_number="B-001", expiry_date=date.today() + timedelta(days=10))
        later = self._batch(batch_number="B-002", expiry_date=date.today() + timedelta(days=900))
        soon.save()
        later.save()
        ordered = list(
            MedicineBatch.objects.filter(medicine=self.medicine).values_list(
                "batch_number", flat=True
            )
        )
        self.assertEqual(ordered, ["B-001", "B-002"])
