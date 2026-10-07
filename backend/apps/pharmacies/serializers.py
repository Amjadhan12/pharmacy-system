"""Serializers for pharmacy (tenant) endpoints."""

from rest_framework import serializers

from .models import Pharmacy, PharmacyProfile


class PharmacyProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PharmacyProfile
        fields = [
            "logo",
            "license_number",
            "license_expiry",
            "description",
            "established_date",
            "opening_hours",
            "social_links",
            "created_at",
            "updated_at",
        ]


class PharmacySerializer(serializers.ModelSerializer):
    owner = serializers.SlugRelatedField(read_only=True, slug_field="email")
    profile = PharmacyProfileSerializer(read_only=True)

    class Meta:
        model = Pharmacy
        fields = [
            "id",
            "owner",
            "name",
            "legal_name",
            "registration_number",
            "tax_number",
            "email",
            "phone",
            "website",
            "address",
            "city",
            "country",
            "latitude",
            "longitude",
            "timezone",
            "currency",
            "tax_rate",
            "tax_enabled",
            "status",
            "profile",
            "created_at",
            "updated_at",
        ]
