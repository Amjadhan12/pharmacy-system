from rest_framework import serializers

from .models import Supplier


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = [
            "id", "pharmacy", "name", "legal_name", "email", "phone", "website",
            "tax_number", "account_bank", "account_number", "address", "city",
            "country", "payment_terms_days", "currency", "is_active",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
