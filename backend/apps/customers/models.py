from django.db import models

from common.utils import TimeStampedModel


class Customer(TimeStampedModel):
    """A person (patient/patient-supplier) who places orders or purchases at a pharmacy.

    Multi-tenant: every customer belongs to exactly one pharmacy.
    """

    pharmacy = models.ForeignKey(
        "pharmacies.Pharmacy", on_delete=models.CASCADE, related_name="customers"
    )
    first_name = models.CharField(max_length=100, default="", blank=True)
    last_name = models.CharField(max_length=100, default="", blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=2, default="PK", blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["last_name", "first_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["pharmacy", "email"],
                name="uniq_customer_email_per_pharmacy",
            )
        ]
        indexes = [
            models.Index(fields=["phone"], name="customer_phone_idx"),
        ]

    def __str__(self) -> str:
        name = " ".join(filter(None, [self.first_name, self.last_name]))
        return name or self.email or f"Customer #{self.pk}"
