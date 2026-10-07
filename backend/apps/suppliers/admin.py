from django.contrib import admin

from .models import Supplier


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("name", "legal_name", "email", "phone", "pharmacy", "is_active", "created_at")
    list_filter = ("is_active", "pharmacy")
    search_fields = ("name", "legal_name", "email", "phone", "tax_number")
    autocomplete_fields = ["pharmacy"]
