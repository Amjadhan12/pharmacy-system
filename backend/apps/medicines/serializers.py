"""Serializers for medicine catalog, categories, dosage forms, manufacturers and batches."""

from datetime import date, timedelta

from rest_framework import serializers

from apps.accounts.tenancy import accessible_pharmacies
from apps.pharmacies.models import Pharmacy
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
        fields = [
            "id", "name", "code", "description", "is_active",
            "created_at", "updated_at",
        ]


class ManufacturerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Manufacturer
        fields = [
            "id", "name", "country", "website", "description", "is_active",
            "created_at", "updated_at",
        ]


class MedicineSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    manufacturer_name = serializers.CharField(
        source="manufacturer.name", read_only=True, allow_null=True
    )
    dosage_form_name = serializers.CharField(
        source="dosage_form.name", read_only=True
    )
    pharmacy = serializers.PrimaryKeyRelatedField(
        queryset=Pharmacy.objects.all(),
        required=False,
    )
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
            "pharmacy",
            "generic_name",
            "brand_name",
            "category_name",
            "manufacturer_name",
            "dosage_form_name",
            "manufacturer",
            "category",
            "dosage_form",
            "strength",
            "route",
            "barcode",
            "gtin",
            "description",
            "prescription_required",
            "reorder_level",
            "storage_condition",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        for identifier in ("barcode", "gtin"):
            if attrs.get(identifier) == "":
                attrs[identifier] = None
        pharmacy = attrs.get("pharmacy")
        if pharmacy is None and self.instance is not None:
            pharmacy = self.instance.pharmacy
        request = self.context.get("request")
        if pharmacy is None and request and self.instance is None:
            pharmacies = accessible_pharmacies(request.user)
            if pharmacies.count() == 1:
                pharmacy = pharmacies.get()
                attrs["pharmacy"] = pharmacy
            elif not pharmacies.exists():
                raise serializers.ValidationError(
                    {"pharmacy": "No accessible pharmacy is available."}
                )
        if pharmacy and request:
            if not accessible_pharmacies(request.user).filter(pk=pharmacy.pk).exists():
                raise serializers.ValidationError(
                    {"pharmacy": "You cannot use this pharmacy."}
                )
        if self.instance and pharmacy and pharmacy.pk != self.instance.pharmacy_id:
            raise serializers.ValidationError(
                {"pharmacy": "A medicine cannot be moved to another pharmacy."}
            )
        # Barcode & GTIN are optional on create but must stay unique when set.
        if "barcode" in attrs and attrs["barcode"]:
            if Medicine.objects.filter(
                pharmacy=pharmacy, barcode=attrs["barcode"]
            ).exclude(
                pk=self.instance.pk if self.instance else None
            ).exists():
                raise serializers.ValidationError(
                    {"barcode": "This barcode is already in use."}
                )
        if "gtin" in attrs and attrs["gtin"]:
            if Medicine.objects.filter(
                pharmacy=pharmacy, gtin=attrs["gtin"]
            ).exclude(
                pk=self.instance.pk if self.instance else None
            ).exists():
                raise serializers.ValidationError({"gtin": "This GTIN is already in use."})
        return attrs


class MedicineBatchSerializer(serializers.ModelSerializer):
    medicine_name = serializers.SerializerMethodField()
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    warehouse_name = serializers.CharField(
        source="warehouse.name", read_only=True, allow_null=True
    )
    status = serializers.SerializerMethodField()

    class Meta:
        model = MedicineBatch
        fields = [
            "id",
            "medicine",
            "medicine_name",
            "branch",
            "branch_name",
            "warehouse",
            "warehouse_name",
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
        read_only_fields = ["id", "status", "created_at", "updated_at"]

    def get_medicine_name(self, obj):
        return str(obj.medicine)

    def get_status(self, obj):
        if obj.expiry_date < date.today():
            return "expired"
        if obj.quantity == 0:
            return "out_of_stock"
        if obj.expiry_date <= date.today() + timedelta(days=30):
            return "expiring"
        return obj.status

    def get_fields(self):
        fields = super().get_fields()
        if self.instance is not None:
            fields["quantity"].read_only = True
        return fields

    def validate(self, attrs):
        branch = attrs.get("branch", self.instance.branch if self.instance else None)
        warehouse = attrs.get(
            "warehouse", self.instance.warehouse if self.instance else None
        )
        if warehouse and branch and warehouse.branch_id != branch.pk:
            raise serializers.ValidationError(
                {"warehouse": "Warehouse must belong to the selected branch."}
            )
        medicine = attrs.get(
            "medicine", self.instance.medicine if self.instance else None
        )
        if medicine and branch and medicine.pharmacy_id not in (None, branch.pharmacy_id):
            raise serializers.ValidationError(
                {"medicine": "Medicine does not belong to the selected pharmacy."}
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
