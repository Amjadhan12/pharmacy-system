from rest_framework import serializers

from apps.accounts.tenancy import accessible_branches
from apps.branches.models import Warehouse
from apps.medicines.models import MedicineBatch
from .models import InventoryTransaction


class InventoryTransactionSerializer(serializers.ModelSerializer):
    batch_number = serializers.CharField(source="batch.batch_number", read_only=True)
    medicine_name = serializers.SerializerMethodField()
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    warehouse_name = serializers.CharField(
        source="warehouse.name", read_only=True, allow_null=True
    )

    class Meta:
        model = InventoryTransaction
        fields = [
            "id",
            "transaction_type",
            "direction",
            "batch",
            "batch_number",
            "medicine",
            "medicine_name",
            "branch",
            "branch_name",
            "warehouse",
            "warehouse_name",
            "quantity",
            "unit_price",
            "reference",
            "notes",
            "created_by",
            "created_at",
        ]
        read_only_fields = fields

    def get_medicine_name(self, obj):
        return str(obj.medicine)


class StockMovementSerializer(serializers.Serializer):
    batch = serializers.PrimaryKeyRelatedField(
        queryset=MedicineBatch.objects.none()
    )
    warehouse = serializers.PrimaryKeyRelatedField(
        queryset=Warehouse.objects.all(),
        required=False,
        allow_null=True,
    )
    quantity = serializers.IntegerField(min_value=1)
    unit_price = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=0, required=False, default=0
    )
    reference = serializers.CharField(max_length=120, required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    direction = serializers.ChoiceField(choices=["in", "out"], required=False)

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            branches = accessible_branches(request.user)
            fields["batch"].queryset = MedicineBatch.objects.filter(
                branch__in=branches
            ).select_related("branch")
            fields["warehouse"].queryset = (
                fields["warehouse"].queryset.filter(branch__in=branches)
            )
        return fields

    def validate(self, attrs):
        batch = attrs["batch"]
        warehouse = attrs.get("warehouse")
        if batch.medicine.pharmacy_id not in (None, batch.branch.pharmacy_id):
            raise serializers.ValidationError(
                {"batch": "Batch medicine does not belong to its pharmacy."}
            )
        if warehouse and warehouse.branch_id != batch.branch_id:
            raise serializers.ValidationError(
                {"warehouse": "Warehouse must belong to the batch branch."}
            )
        return attrs


class StockTransferSerializer(serializers.Serializer):
    source_batch = serializers.PrimaryKeyRelatedField(
        queryset=MedicineBatch.objects.none()
    )
    destination_batch = serializers.PrimaryKeyRelatedField(
        queryset=MedicineBatch.objects.none()
    )
    quantity = serializers.IntegerField(min_value=1)
    reference = serializers.CharField(max_length=120, required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            batches = MedicineBatch.objects.filter(
                branch__in=accessible_branches(request.user)
            ).select_related("branch", "medicine")
            fields["source_batch"].queryset = batches
            fields["destination_batch"].queryset = batches
        return fields

    def validate(self, attrs):
        source = attrs["source_batch"]
        destination = attrs["destination_batch"]
        if source.pk == destination.pk:
            raise serializers.ValidationError(
                {"destination_batch": "Choose a different destination batch."}
            )
        if source.medicine_id != destination.medicine_id:
            raise serializers.ValidationError(
                {"destination_batch": "Transfers must use batches of the same medicine."}
            )
        if source.branch.pharmacy_id != destination.branch.pharmacy_id:
            raise serializers.ValidationError(
                {"destination_batch": "Transfers cannot cross pharmacy tenants."}
            )
        return attrs
