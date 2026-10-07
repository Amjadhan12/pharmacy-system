from django.contrib import admin

from .models import JournalEntry, JournalLine, LedgerAccount


@admin.register(LedgerAccount)
class LedgerAccountAdmin(admin.ModelAdmin):
    list_display = (
        "account_code", "name", "account_type", "currency", "pharmacy", "is_active", "created_at"
    )
    list_filter = ("account_type", "is_active", "pharmacy")
    search_fields = ("account_code", "name", "description")
    autocomplete_fields = ["pharmacy"]


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ("journal_code", "entry_date", "reference", "description", "is_balanced", "is_open", "created_at")
    list_filter = ("is_open", "entry_date")
    search_fields = ("journal_code", "reference", "description")
    readonly_fields = ("debit_total", "credit_total", "is_balanced")

    def debit_total(self, obj):
        return f"{obj.debit_total:.2f}"
    debit_total.short_description = "Debit total"

    def credit_total(self, obj):
        return f"{obj.credit_total:.2f}"
    credit_total.short_description = "Credit total"

    def is_balanced(self, obj):
        return obj.is_balanced
    is_balanced.short_description = "Balanced"


@admin.register(JournalLine)
class JournalLineAdmin(admin.ModelAdmin):
    list_display = ("entry", "account", "debit", "credit")
    list_filter = ("entry",)
    search_fields = ("entry__journal_code", "account__account_code", "account__name")
    raw_id_fields = ("entry", "account")
