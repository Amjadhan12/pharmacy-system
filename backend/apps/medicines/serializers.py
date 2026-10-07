"""Serializers for medicine catalog, categories, dosage forms, manufacturers and batches."""

from django.core.validators import MinValueValidator
from rest_framework import serializers

from .models import (
    DosageForm,
    Manufacturer,
    Medicine,
    MedicineBatch,
    MedicineCategory,
)


class MedicineCategorySerializer(serializers.ModelSerializer):
    parent = serializers.PrimaryKeyRelatedField(
        queryset=MedicineCategory.objects.filter(is_active=True), required=False
    )

    class Meta:
        model = MedicineCategory
        fields = [
            "id",
            "name",
            "code",
            "parent",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        ]


class DosageFormSerializer(serializers.ModelSerializer):
    class Meta:
        model = DosageForm
        fields = ["id", "name", "code", "description", "created_at", "updated_at"]


class ManufacturerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Manufacturer
        fields = ["id", "name", "country", "website", "description", "created_at", "updated_at"]


class MedicineSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(
        queryset=MedicineCategory.objects.filter(is_active=True)
    )
    manufacturer = serializers.PrimaryKeyRelatedField(
        queryset=Manufacturer.objects.all(), required=False
    )
    dosage_form = serializers.PrimaryKeyRelatedField(
        queryset=DosageForm.objects.all()
    )

    class Meta:
        model = Medicine
        fields = [
            "id",
            "generic_name",
            "brand_name",
            "manufacturer",
            "category",
            "dosage_form",
            "strength",
            "route",
            "barcode",
            "gtin",
            "description",
            "prescription_required",
            "storage_condition",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        # Barcode & GTIN are optional on create but must stay unique when set.
        if "barcode" in attrs and attrs["barcode"]:
            if Medicine.objects.filter(barcode=attrs["barcode"]).exclude(
                pk=self.instance.pk if self.instance else None
            ).exists():
                raise serializers.ValidationError(
                    {"barcode": "This barcode is already in use."}
                )
        if "gtin" in attrs and attrs["gtin"]:
            if Medicine.objects.filter(gtin=attrs["gtin"]).exclude(
                pk=self.instance.pk if self.instance else None
            ).exists():
                raise serializers.ValidationError({"gtin": "This GTIN is already in use."})
        return attrs


class MedicineBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicineBatch
        fields = [
            "id",
            "medicine",
            "branch",
            "warehouse",
            "batch_number",
            "purchase_price",
            "selling_price",
            "quantity",
            "manufacture_date",
            "expiry_date",
            "barcode",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        branch = attrs.get("branch", self.instance.branch if self.instance else None)
        warehouse = attrs.get(
            "warehouse", self.instance.warehouse if self.instance else None
        )
        if warehouse and branch and warehouse.branch_id != branch.pk:
            raise serializers.ValidationError(
                {"warehouse": "Warehouse must belong to the selected branch."}
            )

        purchase_price = attrs.get("purchase_price")
        selling_price = attrs.get("selling_price")
        manufacture_date = attrs.get("manufacture_date")
        expiry_date = attrs.get("expiry_date")

        if purchase_price is not None and purchase_price < 0:
            raise serializers.ValidationError(
                {"purchase_price": "Must be 0 or greater."}
            )
        if selling_price is not None and selling_price < 0:
            raise serializers.ValidationError({"selling_price": "Must be 0 or greater."})
        if manufacture_date and expiry_date and manufacture_date > expiry_date:
            raise serializers.ValidationError(
                {"expiry_date": "Must be on or after manufacture date."}
            )
        return attrs
