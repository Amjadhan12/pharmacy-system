from django.contrib import admin

from .models import InventoryTransaction


@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "transaction_type",
        "batch",
        "medicine",
        "branch",
        "quantity",
        "unit_price",
        "reference",
        "created_at",
    )
    list_filter = ("transaction_type", "batch__medicine", "created_at")
    search_fields = ("reference", "batch__batch_number", "medicine__generic_name")
    autocomplete_fields = ["batch", "medicine", "branch", "created_by"]
