"""Medicine catalog and batch models."""
from django.core.validators import MinValueValidator
from django.db import models

from common.constants import BatchStatus, MedicineRoute, StorageCondition
from common.utils import TimeStampedModel


class MedicineCategory(TimeStampedModel):
    """Hierarchical medicine category (e.g. Analgesics > NSAIDs)."""

    name = models.CharField(max_length=150)
    code = models.SlugField(max_length=64, unique=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["name", "parent"], name="uniq_category_name_parent"
            ),
        ]

    def __str__(self) -> str:
        return self.name


class DosageForm(TimeStampedModel):
    """Medicine dosage form (tablet, capsule, syrup, ...)."""

    name = models.CharField(max_length=100, unique=True)
    code = models.SlugField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Manufacturer(TimeStampedModel):
    """Medicine manufacturer."""

    name = models.CharField(max_length=150, unique=True)
    country = models.CharField(max_length=2, blank=True)
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Medicine(TimeStampedModel):
    """A tenant-owned medicine product (generic/brand level, not per-batch).

    A null pharmacy is reserved for shared legacy/formulary entries.
    """

    pharmacy = models.ForeignKey(
        "pharmacies.Pharmacy",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="medicines",
        help_text="Null only for a shared formulary entry.",
    )
    generic_name = models.CharField(max_length=200, db_index=True)
    brand_name = models.CharField(max_length=200, blank=True, db_index=True)
    manufacturer = models.ForeignKey(
        Manufacturer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="medicines",
    )
    category = models.ForeignKey(
        MedicineCategory,
        on_delete=models.PROTECT,
        related_name="medicines",
    )
    dosage_form = models.ForeignKey(
        DosageForm,
        on_delete=models.PROTECT,
        related_name="medicines",
    )
    strength = models.CharField(
        max_length=100, blank=True, help_text='e.g. "500 mg", "10 mg/5 ml"'
    )
    route = models.CharField(
        max_length=30,
        choices=MedicineRoute.choices,
        default=MedicineRoute.ORAL,
    )
    barcode = models.CharField(max_length=64, null=True, blank=True)
    gtin = models.CharField(
        max_length=20, null=True, blank=True, verbose_name="GTIN"
    )
    description = models.TextField(blank=True)
    prescription_required = models.BooleanField(default=False)
    reorder_level = models.PositiveIntegerField(default=10)
    storage_condition = models.CharField(
        max_length=30,
        choices=StorageCondition.choices,
        default=StorageCondition.ROOM_TEMPERATURE,
    )
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["generic_name", "brand_name"]
        indexes = [
            models.Index(
                fields=["generic_name", "brand_name"], name="medicine_name_idx"
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["pharmacy", "barcode"],
                name="uniq_medicine_pharmacy_barcode",
            ),
            models.UniqueConstraint(
                fields=["pharmacy", "gtin"],
                name="uniq_medicine_pharmacy_gtin",
            ),
        ]

    def __str__(self) -> str:
        base = self.brand_name or self.generic_name
        return f"{base} {self.strength}".strip()


class MedicineBatch(TimeStampedModel):
    """A purchasable batch of a medicine at a specific branch/warehouse.

    This is the unit of inventory: quantity, prices and expiry live here.
    """

    medicine = models.ForeignKey(
        Medicine, on_delete=models.PROTECT, related_name="batches"
    )
    branch = models.ForeignKey(
        "branches.Branch", on_delete=models.CASCADE, related_name="medicine_batches"
    )
    warehouse = models.ForeignKey(
        "branches.Warehouse",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="medicine_batches",
    )
    batch_number = models.CharField(max_length=100, db_index=True)
    purchase_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    selling_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    quantity = models.PositiveIntegerField(default=0)
    manufacture_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(db_index=True)
    barcode = models.CharField(max_length=64, unique=True, null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=BatchStatus.choices,
        default=BatchStatus.AVAILABLE,
        db_index=True,
    )

    class Meta:
        ordering = ["expiry_date"]  # FEFO-friendly default
        constraints = [
            models.UniqueConstraint(
                fields=["branch", "medicine", "batch_number"],
                name="uniq_batch_per_branch_medicine",
            ),
            models.CheckConstraint(
                condition=models.Q(purchase_price__gte=0),
                name="batch_purchase_price_non_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(selling_price__gte=0),
                name="batch_selling_price_non_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(manufacture_date__isnull=True)
                | models.Q(manufacture_date__lte=models.F("expiry_date")),
                name="batch_manufacture_before_expiry",
            ),
        ]
        indexes = [
            models.Index(
                fields=["branch", "expiry_date"], name="batch_branch_expiry_idx"
            ),
            models.Index(
                fields=["medicine", "status"], name="batch_medicine_status_idx"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.medicine} [{self.batch_number}] ({self.branch.code})"

    @property
    def is_expired(self) -> bool:
        from datetime import date

        return self.expiry_date < date.today()
