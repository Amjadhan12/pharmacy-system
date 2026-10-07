from django.contrib import admin

from .models import Pharmacy, PharmacyProfile


class PharmacyProfileInline(admin.StackedInline):
    model = PharmacyProfile
    can_delete = False


@admin.register(Pharmacy)
class PharmacyAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "city",
        "country",
        "currency",
        "status",
        "owner",
        "created_at",
    )
    list_filter = ("status", "country", "currency")
    search_fields = ("name", "legal_name", "registration_number", "tax_number", "owner__email")
    inlines = [PharmacyProfileInline]


@admin.register(PharmacyProfile)
class PharmacyProfileAdmin(admin.ModelAdmin):
    list_display = ("pharmacy", "license_number", "license_expiry")
    search_fields = ("pharmacy__name", "license_number")
