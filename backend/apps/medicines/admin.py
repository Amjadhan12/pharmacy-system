from django.contrib import admin

from .models import DosageForm, Manufacturer, Medicine, MedicineBatch, MedicineCategory


@admin.register(MedicineCategory)
class MedicineCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "parent", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "code")


@admin.register(DosageForm)
class DosageFormAdmin(admin.ModelAdmin):
    list_display = ("name", "code")
    search_fields = ("name", "code")


@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    list_display = ("name", "country", "website")
    search_fields = ("name", "country")


class MedicineBatchInline(admin.TabularInline):
    model = MedicineBatch
    extra = 0
    fields = (
        "batch_number",
        "branch",
        "warehouse",
        "quantity",
        "purchase_price",
        "selling_price",
        "expiry_date",
        "status",
    )


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = (
        "generic_name",
        "brand_name",
        "strength",
        "dosage_form",
        "category",
        "prescription_required",
        "is_active",
    )
    list_filter = ("dosage_form", "prescription_required", "is_active", "category")
    search_fields = ("generic_name", "brand_name", "barcode", "gtin")
    inlines = [MedicineBatchInline]


@admin.register(MedicineBatch)
class MedicineBatchAdmin(admin.ModelAdmin):
    list_display = (
        "medicine",
        "batch_number",
        "branch",
        "quantity",
        "purchase_price",
        "selling_price",
        "expiry_date",
        "status",
    )
    list_filter = ("status", "branch")
    search_fields = ("batch_number", "barcode", "medicine__generic_name", "medicine__brand_name")
