"""Pharmacy (tenant) models."""
from django.db import models

from common.constants import PharmacyStatus
from common.utils import TimeStampedModel


class Pharmacy(TimeStampedModel):
    """A pharmacy business (the tenant of the platform)."""

    owner = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="pharmacies",
    )
    name = models.CharField(max_length=150, db_index=True)
    legal_name = models.CharField(max_length=150, blank=True)
    registration_number = models.CharField(max_length=100, blank=True, db_index=True)
    tax_number = models.CharField(max_length=100, blank=True)

    # Contact & location
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    website = models.URLField(blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True, db_index=True)
    country = models.CharField(max_length=2, db_index=True)  # ISO 3166-1 alpha-2
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )

    # Localization
    timezone = models.CharField(max_length=63, default="UTC")  # IANA name
    currency = models.CharField(max_length=3, default="USD")  # ISO 4217

    # Tax settings
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Default VAT/sales tax rate in percent.",
    )
    tax_enabled = models.BooleanField(default=True)

    status = models.CharField(
        max_length=20,
        choices=PharmacyStatus.choices,
        default=PharmacyStatus.ACTIVE,
        db_index=True,
    )

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name", "city"], name="pharmacy_name_city_idx"),
        ]

    def __str__(self) -> str:
        return self.name


class PharmacyProfile(TimeStampedModel):
    """Extended profile information for a pharmacy."""

    pharmacy = models.OneToOneField(
        Pharmacy, on_delete=models.CASCADE, related_name="profile"
    )
    logo = models.ImageField(upload_to="pharmacy/logos/", blank=True, null=True)
    license_number = models.CharField(max_length=100, blank=True)
    license_expiry = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    established_date = models.DateField(null=True, blank=True)
    opening_hours = models.JSONField(
        default=dict, blank=True
    )  # {"mon": "09:00-21:00", ...}
    social_links = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:
        return f"Profile of {self.pharmacy.name}"
