from rest_framework import serializers

from apps.accounts.tenancy import accessible_branches
from apps.branches.models import Warehouse
from apps.medicines.models import MedicineBatch
from .models import InventoryTransaction


class InventoryTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryTransaction
        fields = [
            "id",
            "transaction_type",
            "direction",
            "batch",
            "medicine",
            "branch",
            "warehouse",
            "quantity",
            "unit_price",
            "reference",
            "created_by",
            "created_at",
        ]
        read_only_fields = fields


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
        if warehouse and warehouse.branch_id != batch.branch_id:
            raise serializers.ValidationError(
                {"warehouse": "Warehouse must belong to the batch branch."}
            )
        return attrs
