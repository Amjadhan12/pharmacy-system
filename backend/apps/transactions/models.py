from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

from common.utils import TimeStampedModel


class InventoryTransaction(TimeStampedModel):
    """Immutable ledger of every change to batch quantity (stock movements)."""

    TRANSACTION_TYPES = [
        ("purchase", "Purchase"),
        ("sale", "Sale"),
        ("sale_return", "Sale return"),
        ("purchase_return", "Purchase return"),
        ("adjustment_in", "Adjustment in"),
        ("adjustment_out", "Adjustment out"),
        ("transfer_in", "Transfer in"),
        ("transfer_out", "Transfer out"),
        ("damage", "Damaged stock"),
        ("expired", "Expired stock"),
        ("receipt", "Stock receipt (purchase)"),
        ("dispatch", "Stock dispatch (sale)"),
        ("transfer", "Internal transfer between branches"),
        ("adjustment", "Manual adjustment"),
        ("return", "Customer/supplier return"),
    ]
    DIRECTIONS = [("in", "Stock in"), ("out", "Stock out")]

    transaction_type = models.CharField(
        max_length=20, choices=TRANSACTION_TYPES, db_index=True
    )
    direction = models.CharField(max_length=3, choices=DIRECTIONS, default="in")
    batch = models.ForeignKey(
        "medicines.MedicineBatch",
        on_delete=models.PROTECT,
        related_name="ledger",
        db_index=True,
    )
    medicine = models.ForeignKey(
        "medicines.Medicine", on_delete=models.PROTECT, db_index=True
    )
    branch = models.ForeignKey(
        "branches.Branch",
        on_delete=models.PROTECT,
        related_name="inventory_transactions",
    )
    warehouse = models.ForeignKey(
        "branches.Warehouse",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inventory_transactions",
    )
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0"))]
    )
    reference = models.CharField(max_length=120, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, related_name="inventory_transactions"
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["batch", "-created_at"], name="txn_batch_latest_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.get_transaction_type_display()}: {self.batch.batch_number} x{self.quantity}"
