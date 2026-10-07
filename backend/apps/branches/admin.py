from django.contrib import admin

from .models import Branch, Warehouse


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "pharmacy", "city", "status", "is_default")
    list_filter = ("status", "is_default", "pharmacy")
    search_fields = ("name", "code", "city", "pharmacy__name")


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "branch", "is_active", "is_default")
    list_filter = ("is_active", "is_default")
    search_fields = ("name", "code", "branch__name")
