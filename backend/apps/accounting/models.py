from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

from common.utils import TimeStampedModel

# Natural balance: increases on the side shown.
DEBIT_NORMAL_TYPES = {
    "asset", "expense", "contra_asset", "contra_expense", "contra_revenue", "contra_liability"
}
CREDIT_NORMAL_TYPES = {
    "liability", "equity", "revenue", "contra_liability", "contra_revenue"
}
ACCOUNT_TYPES = [
    ("asset", "Asset"),
    ("liability", "Liability"),
    ("equity", "Equity"),
    ("revenue", "Revenue"),
    ("expense", "Expense"),
    ("contra_asset", "Contra Asset"),
    ("contra_liability", "Contra Liability"),
    ("contra_revenue", "Contra Revenue"),
    ("contra_expense", "Contra Expense"),
]


class LedgerAccount(TimeStampedModel):
    """A chart-of-accounts account scoped to one pharmacy."""

    account_code = models.CharField(
        max_length=20, unique=True, db_index=True, help_text="e.g. 1000 - Cash at Bank"
    )
    name = models.CharField(max_length=120)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    currency = models.CharField(max_length=3, default="PKR")
    pharmacy = models.ForeignKey(
        "pharmacies.Pharmacy", on_delete=models.CASCADE, related_name="accounts"
    )
    parent = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="children"
    )
    position_order = models.IntegerField(default=0, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["pharmacy", "position_order"]
        indexes = [
            models.Index(fields=["pharmacy", "account_code"], name="acct_code_ph_idx"),
        ]

    @property
    def increase_side(self) -> str:
        return "Debit" if self.account_type in DEBIT_NORMAL_TYPES else "Credit"

    @property
    def decrease_side(self) -> str:
        return "Credit" if self.increase_side == "Debit" else "Debit"

    def __str__(self) -> str:
        return self.account_code + " - " + self.name


class JournalEntry(TimeStampedModel):
    """A single accounting entry; its debit lines must equal its credit lines."""

    journal_code = models.CharField(
        max_length=20, unique=True, db_index=True, help_text="e.g. JE-20261007-00001"
    )
    entry_date = models.DateField(db_index=True)
    reference = models.CharField(max_length=120, blank=True)
    description = models.TextField(blank=True)
    is_open = models.BooleanField(default=True, db_index=True)
    created_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, related_name="journal_entries"
    )

    class Meta:
        ordering = ["-entry_date", "-id"]
        indexes = [
            models.Index(fields=["entry_date", "is_open"], name="je_open_date_idx"),
        ]

    @property
    def debit_total(self) -> Decimal:
        return sum((line.debit for line in self.lines.all()), Decimal("0"))

    @property
    def credit_total(self) -> Decimal:
        return sum((line.credit for line in self.lines.all()), Decimal("0"))

    @property
    def is_balanced(self) -> bool:
        return self.debit_total == self.credit_total

    def __str__(self) -> str:
        return f"{self.journal_code} ({self.entry_date}) {self.description or ''}"


class JournalLine(TimeStampedModel):
    """One account movement within a journal entry."""

    entry = models.ForeignKey(
        JournalEntry, on_delete=models.CASCADE, related_name="lines"
    )
    account = models.ForeignKey(
        LedgerAccount, on_delete=models.PROTECT, db_index=True
    )
    debit = models.DecimalField(
        max_digits=16, decimal_places=2, default=Decimal("0"),
        validators=[MinValueValidator(Decimal("0"))],
    )
    credit = models.DecimalField(
        max_digits=16, decimal_places=2, default=Decimal("0"),
        validators=[MinValueValidator(Decimal("0"))],
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["entry", "account"], name="uniq_journal_line_account"),
            models.CheckConstraint(
                condition=(
                    (models.Q(debit__gte=0) & models.Q(credit__gte=0))
                ),
                name="jline_non_negative",
            ),
        ]
        indexes = [models.Index(fields=["entry", "account"], name="jline_entry_account_idx")]

    @property
    def balance(self) -> Decimal:
        return self.debit - self.credit

    def __str__(self) -> str:
        return f"{self.account.account_code} {self.account.name}: Dr {self.debit} Cr {self.credit}"
