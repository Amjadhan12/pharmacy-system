"""Serializers for branch and warehouse endpoints."""

from rest_framework import serializers

from .models import Branch, Warehouse


class BranchSerializer(serializers.ModelSerializer):
    manager = serializers.SlugRelatedField(read_only=True, slug_field="email")

    class Meta:
        model = Branch
        fields = [
            "id",
            "pharmacy",
            "name",
            "code",
            "address",
            "city",
            "phone",
            "email",
            "latitude",
            "longitude",
            "opening_time",
            "closing_time",
            "manager",
            "is_default",
            "status",
            "created_at",
            "updated_at",
        ]


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = [
            "id",
            "name",
            "code",
            "branch",
            "is_active",
            "is_default",
            "created_at",
            "updated_at",
        ]
