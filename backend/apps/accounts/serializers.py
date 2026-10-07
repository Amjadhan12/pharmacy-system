from rest_framework import serializers

from apps.accounts.tenancy import accessible_branches, accessible_pharmacies
from .models import Role, User


class PharmacyAccessSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    city = serializers.CharField()
    country = serializers.CharField()
    currency = serializers.CharField()


class BranchAccessSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    code = serializers.CharField()
    pharmacy_id = serializers.IntegerField()
    is_default = serializers.BooleanField()


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["id", "name", "code", "description"]
        read_only_fields = fields


class UserSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)
    full_name = serializers.CharField(read_only=True)
    pharmacies = serializers.SerializerMethodField()
    branches = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()

    def get_pharmacies(self, obj):
        return PharmacyAccessSerializer(
            accessible_pharmacies(obj).order_by("name"), many=True
        ).data

    def get_branches(self, obj):
        return BranchAccessSerializer(
            accessible_branches(obj).order_by("name"), many=True
        ).data

    def get_permissions(self, obj):
        if obj.role_id is None:
            return []
        return list(
            obj.role.role_permissions.order_by("permission__code").values_list(
                "permission__code", flat=True
            )
        )

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "full_name",
            "phone",
            "avatar",
            "role",
            "pharmacies",
            "branches",
            "permissions",
            "is_active",
            "date_joined",
        ]
        read_only_fields = ["id", "date_joined", "is_active"]
