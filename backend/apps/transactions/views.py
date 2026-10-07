from django.db.models import QuerySet
from rest_framework import generics, permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.tenancy import accessible_branches
from apps.medicines.models import MedicineBatch
from .models import InventoryTransaction
from .serializers import InventoryTransactionSerializer, StockMovementSerializer
from .services import record_stock_movement


class InventoryTransactionListView(generics.ListAPIView):
    serializer_class = InventoryTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        qs = InventoryTransaction.objects.filter(
            branch__in=accessible_branches(self.request.user)
        ).select_related("batch", "medicine", "branch", "warehouse", "created_by")
        branch = self.request.query_params.get("branch")
        batch = self.request.query_params.get("batch")
        movement_type = self.request.query_params.get("transaction_type")
        if branch:
            qs = qs.filter(branch_id=branch)
        if batch:
            qs = qs.filter(batch_id=batch)
        if movement_type:
            qs = qs.filter(transaction_type=movement_type)
        return qs


class StockMovementView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    movement_types = {"receipt", "dispatch", "adjustment", "return"}

    def post(self, request, transaction_type):
        if transaction_type not in self.movement_types:
            raise serializers.ValidationError(
                {"transaction_type": "Unsupported inventory movement."}
            )
        if not (
            request.user.is_superuser
            or request.user.has_role(
                "pharmacy_owner",
                "pharmacy_manager",
                "pharmacist",
                "inventory_manager",
            )
        ):
            self.permission_denied(request)

        payload = StockMovementSerializer(data=request.data, context={"request": request})
        payload.is_valid(raise_exception=True)
        data = payload.validated_data
        batch: MedicineBatch = data["batch"]
        movement = record_stock_movement(
            transaction_type=transaction_type,
            batch=batch,
            branch=batch.branch,
            warehouse=data.get("warehouse", batch.warehouse),
            quantity=data["quantity"],
            unit_price=data.get("unit_price", batch.purchase_price),
            reference=data.get("reference", ""),
            created_by=request.user,
            direction=data.get("direction"),
        )
        return Response(
            InventoryTransactionSerializer(movement).data,
            status=status.HTTP_201_CREATED,
        )
