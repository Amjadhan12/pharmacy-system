"""Shared choice enumerations used across PharmaFin apps."""
from django.db import models


class PharmacyStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    SUSPENDED = "suspended", "Suspended"


class BranchStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"


class MedicineRoute(models.TextChoices):
    ORAL = "oral", "Oral"
    TOPICAL = "topical", "Topical"
    SUBLINGUAL = "sublingual", "Sublingual"
    INTRAVENOUS = "intravenous", "Intravenous"
    INTRAMUSCULAR = "intramuscular", "Intramuscular"
    SUBCUTANEOUS = "subcutaneous", "Subcutaneous"
    INHALATION = "inhalation", "Inhalation"
    OPHTHALMIC = "ophthalmic", "Ophthalmic"
    OTIC = "otic", "Otic"
    NASAL = "nasal", "Nasal"
    RECTAL = "rectal", "Rectal"
    VAGINAL = "vaginal", "Vaginal"
    OTHER = "other", "Other"


class StorageCondition(models.TextChoices):
    ROOM_TEMPERATURE = "room_temperature", "Room Temperature"
    COOL = "cool", "Cool (2-8 °C)"
    COLD = "cold", "Cold (2-8 °C)"  # kept distinct from cool for labeling
    FROZEN = "frozen", "Frozen (-20 °C)"
    DRY = "dry", "Dry"
    PROTECT_FROM_LIGHT = "protect_from_light", "Protect From Light"


class BatchStatus(models.TextChoices):
    AVAILABLE = "available", "Available"
    RESERVED = "reserved", "Reserved"
    EXPIRED = "expired", "Expired"
    RECALLED = "recalled", "Recalled"
    DAMAGED = "damaged", "Damaged"
