from django.db import models

from common.utils import TimeStampedModel


class Supplier(TimeStampedModel):
    """A company that sells medicines or supplies to a pharmacy.

    Multi-tenant: every supplier belongs to one pharmacy, and each pharmacy sees
    only the suppliers it owns.
    """

    pharmacy = models.ForeignKey(
        "pharmacies.Pharmacy", on_delete=models.CASCADE, related_name="suppliers"
    )
    name = models.CharField(max_length=150, db_index=True)
    legal_name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    website = models.URLField(blank=True)
    tax_number = models.CharField(max_length=100, blank=True)
    account_bank = models.CharField(max_length=100, blank=True)
    account_number = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=2, default="PK", blank=True)
    payment_terms_days = models.PositiveIntegerField(default=7)
    currency = models.CharField(max_length=3, default="PKR")
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name", "pharmacy"], name="supplier_name_pharmacy_idx"),
        ]

    def __str__(self) -> str:
        return self.name
