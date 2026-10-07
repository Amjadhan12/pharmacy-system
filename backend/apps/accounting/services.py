from decimal import Decimal

from django.db import transaction
from django.core.exceptions import ValidationError

from apps.pharmacies.models import Pharmacy
from .models import JournalEntry, JournalLine, LedgerAccount


def debit(account: LedgerAccount, amount: Decimal):
    return {"account": account, "amount": amount, "side": "debit"}


def credit(account: LedgerAccount, amount: Decimal):
    return {"account": account, "amount": amount, "side": "credit"}


def _entries_for(moves):
    """Group normalized moves by entry date."""
    groups = {}
    for m in moves:
        date = m.get("entry_date")
        groups.setdefault(date, []).append(m)
    return groups


def record_journal_transactions(
    moves,
    entry_date=None,
    reference="",
    description="",
    created_by=None,
):
    """Create balanced journal entries (debit == credit) for a list of moves.

    ``moves``: list of dict(account=LedgerAccount|int, amount=Decimal|str,
                           side="debit"|"credit", optional entry_date).
    Each date forms one JournalEntry; the entry is rejected unless it balances.
    """
    if not moves:
        return None

    normalized = []
    for m in moves:
        account = m.get("account")
        if isinstance(account, int):
            account = LedgerAccount.objects.filter(pk=account).first()
        elif isinstance(account, str):
            account = LedgerAccount.objects.filter(
                pharmacy=None, account_code=account
            ).first()
        if account is None:
            raise ValidationError(f"Unknown account: {m.get('account')!r}")
        try:
            amount = Decimal(str(m.get("amount", 0)))
        except Exception:
            raise ValidationError(f"Invalid amount: {m.get('amount')!r}")
        if amount < 0:
            raise ValidationError("Amounts must be non-negative.")
        side = m.get("side", "debit")
        if side not in ("debit", "credit"):
            raise ValidationError(f"Invalid side: {side!r}")
        normalized.append({"account": account, "amount": amount, "side": side})

    by_date = _entries_for(normalized)
    entries = []
    for date, group in sorted(by_date.items()):
        totals = {"debit": Decimal("0"), "credit": Decimal("0")}
        for m in group:
            totals[m["side"]] += m["amount"]
        if totals["debit"] != totals["credit"]:
            raise ValidationError(
                f"Unbalanced journal for {date}: debit {totals['debit']} "
                f"!= credit {totals['credit']}. Entries must balance."
            )
        code = f"JE-{date or 'ALL'}-{len(entries) + 1:05d}"
        entry = JournalEntry.objects.create(
            journal_code=code,
            entry_date=date,
            reference=reference,
            description=description,
            created_by=created_by,
        )
        for m in group:
            JournalLine.objects.create(
                entry=entry,
                account=m["account"],
                debit=m["amount"] if m["side"] == "debit" else Decimal("0"),
                credit=m["amount"] if m["side"] == "credit" else Decimal("0"),
            )
        entries.append(entry)

    return entries

def auto_code(prefix: str, pharmacy: Pharmacy, name_hint: str) -> str:
    """Create an unused 4-digit account code under ``prefix`` for a pharmacy."""
    used = set(
        LedgerAccount.objects.filter(pharmacy=pharmacy)
        .values_list("account_code", flat=True)
    )
    n = 1
    while True:
        code = f"{prefix}{n:04d}"
        if code not in used:
            return code
        n += 1


def _seed_defaults(pharmacy):
    return {
        "inventory": (Decimal("0"), Decimal("0"), "Asset", "stock asset"),
        "cash_bank": (Decimal("100000"), Decimal("0"), "Asset", "operating bank account"),
        "accounts_payable": (Decimal("0"), Decimal("0"), "Liability", "supplier payable"),
        "accounts_receivable": (Decimal("0"), Decimal("0"), "Asset", "customer receivable"),
        "sales_revenue": (Decimal("0"), Decimal("0"), "Revenue", "net sales"),
        "sales_tax_payable": (Decimal("0"), Decimal("0"), "Liability", "collected sales tax"),
        "cost_of_goods_sold": (Decimal("0"), Decimal("0"), "Expense", "cost of goods sold"),
        "equity": (Decimal("0"), Decimal("0"), "Equity", "opening equity"),
    }


def seed_chart_of_accounts(pharmacy, created_by=None):
    """Create the standard chart of accounts scoped to one pharmacy."""
    defaults = _seed_defaults(pharmacy)
    payloads = [
        (auto_code("1", pharmacy, "Bank"), "cash_bank", "1000", "Asset", "0", "Operating bank account"),
        (auto_code("1", pharmacy, "Cash"), "cash_on_hand", "1100", "Asset", "0", "Physical cash"),
        (auto_code("1", pharmacy, "Receivable"), "accounts_receivable", "1200", "Asset", "0", "Customer credit"),
        (auto_code("1", pharmacy, "Inventory"), "inventory", "1300", "Asset", "0", "Stock asset"),
        (auto_code("2", pharmacy, "Payable"), "accounts_payable", "2000", "Liability", "0", "Supplier payable"),
        (auto_code("2", pharmacy, "Tax Payable"), "sales_tax_payable", "2100", "Liability", "0", "Sales tax payable"),
        (auto_code("3", pharmacy, "Equity"), "equity", "3000", "Equity", "0", "Opening equity"),
        (auto_code("4", pharmacy, "Sales"), "sales_revenue", "4000", "Revenue", "0", "Net sales revenue"),
        (auto_code("5", pharmacy, "COGS"), "cost_of_goods_sold", "5000", "Expense", "0", "Cost of goods sold"),
        (auto_code("5", pharmacy, "Purchase Returns"), "purchase_returns", "5100", "Contra Expense", "0", "Purchase returns"),
        (auto_code("5", pharmacy, "Rent"), "rent_expense", "5200", "Expense", "0", "Rent expense"),
        (auto_code("5", pharmacy, "Salaries"), "salary_expense", "5201", "Expense", "0", "Salaries expense"),
        (auto_code("5", pharmacy, "Utilities"), "utilities_expense", "5202", "Expense", "0", "Utilities expense"),
        (auto_code("5", pharmacy, "Repair"), "maintenance_expense", "5203", "Expense", "0", "Maintenance & repairs"),
    ]
    created = []
    with transaction.atomic():
        for code, key, atype, name, order, desc in payloads:
            obj, _ = LedgerAccount.objects.get_or_create(
                pharmacy=pharmacy, account_code=code,
                defaults={
                    "name": name,
                    "account_type": atype,
                    "currency": "PKR",
                    "position_order": int(order),
                    "description": desc,
                },
            )
            created.append(obj)
    return created

