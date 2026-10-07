from django.contrib import admin

from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "phone", "pharmacy", "is_active", "created_at")
    list_filter = ("is_active", "pharmacy")
    search_fields = ("first_name", "last_name", "email", "phone")
    autocomplete_fields = ["pharmacy"]

    def full_name(self, obj):
        return " ".join(filter(None, [obj.first_name, obj.last_name]))
    full_name.short_description = "Name"
