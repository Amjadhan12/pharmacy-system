from rest_framework import serializers

from apps.pharmacies.models import Pharmacy  # noqa: F401
from .models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    pharmacy = serializers.PrimaryKeyRelatedField(
        queryset=Pharmacy.objects.all(), write_only=True
    )
    full_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Customer
        fields = [
            "id", "pharmacy", "first_name", "last_name", "full_name", "email",
            "phone", "address", "city", "country", "notes", "is_active",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_full_name(self, obj) -> str:
        return " ".join(filter(None, [obj.first_name, obj.last_name]))
