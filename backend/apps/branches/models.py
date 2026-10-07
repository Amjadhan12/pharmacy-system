"""Branch and warehouse models."""
from django.db import models

from common.constants import BranchStatus
from common.utils import TimeStampedModel


class Branch(TimeStampedModel):
    """A physical branch/shop of a pharmacy."""

    pharmacy = models.ForeignKey(
        "pharmacies.Pharmacy", on_delete=models.CASCADE, related_name="branches"
    )
    name = models.CharField(max_length=150)
    code = models.SlugField(max_length=30)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True, db_index=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    opening_time = models.TimeField(null=True, blank=True)
    closing_time = models.TimeField(null=True, blank=True)
    manager = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_branches",
    )
    is_default = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20,
        choices=BranchStatus.choices,
        default=BranchStatus.ACTIVE,
        db_index=True,
    )

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["pharmacy", "code"], name="uniq_branch_code_per_pharmacy"
            ),
        ]
        indexes = [
            models.Index(fields=["pharmacy", "status"], name="branch_pharmacy_status_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.pharmacy.name} - {self.name}"


class Warehouse(TimeStampedModel):
    """A storage location belonging to a branch."""

    branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, related_name="warehouses"
    )
    name = models.CharField(max_length=150)
    code = models.SlugField(max_length=30)
    address = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["branch", "code"], name="uniq_warehouse_code_per_branch"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.branch.code}/{self.code} - {self.name}"
