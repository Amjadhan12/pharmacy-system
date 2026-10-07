from datetime import date, timedelta

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import F, IntegerField, OuterRef, Q, Subquery, Sum, Value
from django.db.models.functions import Coalesce
from rest_framework import generics, permissions, serializers
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.tenancy import accessible_branches, accessible_pharmacies
from apps.branches.models import Branch
from apps.medicines.models import Medicine, MedicineBatch
from apps.medicines.serializers import MedicineBatchSerializer
from .services import FEFOAllocationService


def visible_medicines(user):
    return Medicine.objects.filter(
        Q(pharmacy__in=accessible_pharmacies(user)) | Q(pharmacy__isnull=True)
    )


def available_stock_subquery(user, branch_id=None):
    batches = MedicineBatch.objects.filter(
        medicine_id=OuterRef("pk"),
        branch__in=accessible_branches(user),
        quantity__gt=0,
        status="available",
        expiry_date__gte=date.today(),
    ).filter(
        Q(medicine__pharmacy__isnull=True)
        | Q(branch__pharmacy_id=F("medicine__pharmacy_id"))
    )
    if branch_id is not None:
        batches = batches.filter(branch_id=branch_id)
    return (
        batches.values("medicine_id")
        .annotate(total=Sum("quantity"))
        .values("total")[:1]
    )


class LowStockMedicineSerializer(serializers.ModelSerializer):
    available_stock = serializers.IntegerField(read_only=True)

    class Meta:
        model = Medicine
        fields = [
            "id",
            "generic_name",
            "brand_name",
            "strength",
            "category",
            "reorder_level",
            "available_stock",
        ]


class LowStockListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LowStockMedicineSerializer

    def get_queryset(self):
        branch_id = self.request.query_params.get("branch")
        branches = accessible_branches(self.request.user)
        if branch_id:
            if not branches.filter(pk=branch_id).exists():
                raise PermissionDenied("You cannot view stock for this branch.")
        medicines = visible_medicines(self.request.user).filter(is_active=True)
        return (
            medicines.annotate(
                available_stock=Coalesce(
                    Subquery(
                        available_stock_subquery(self.request.user, branch_id),
                        output_field=IntegerField(),
                    ),
                    Value(0),
                )
            )
            .filter(available_stock__lt=F("reorder_level"))
            .select_related("category")
            .order_by("generic_name", "id")
        )


class BatchExpiryListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MedicineBatchSerializer

    def get_queryset(self):
        branches = accessible_branches(self.request.user)
        batches = MedicineBatch.objects.filter(
            branch__in=branches,
            quantity__gt=0,
        ).filter(
            Q(medicine__pharmacy__in=accessible_pharmacies(self.request.user))
            | Q(medicine__pharmacy__isnull=True)
        )
        branch_id = self.request.query_params.get("branch")
        if branch_id:
            if not branches.filter(pk=branch_id).exists():
                raise PermissionDenied("You cannot view stock for this branch.")
            batches = batches.filter(branch_id=branch_id)

        if self.request.path.endswith("/expired/"):
            batches = batches.filter(expiry_date__lt=date.today())
        else:
            raw_days = self.request.query_params.get("days", "30")
            try:
                days = int(raw_days)
            except ValueError as exc:
                raise serializers.ValidationError(
                    {"days": "Enter a whole number of days."}
                ) from exc
            if days < 1 or days > 365:
                raise serializers.ValidationError(
                    {"days": "Days must be between 1 and 365."}
                )
            batches = batches.filter(
                expiry_date__gte=date.today(),
                expiry_date__lte=date.today() + timedelta(days=days),
            )
        return batches.select_related(
            "medicine", "medicine__category", "branch", "warehouse"
        ).order_by("expiry_date", "id")


class FEFOAvailabilityView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, medicine_id):
        medicine = visible_medicines(request.user).filter(
            pk=medicine_id, is_active=True
        ).first()
        if medicine is None:
            raise NotFound("Medicine not found.")
        branch_id = request.query_params.get("branch")
        if not branch_id:
            raise serializers.ValidationError(
                {"branch": "A branch is required for FEFO allocation."}
            )
        branch = Branch.objects.filter(
            pk=branch_id, pk__in=accessible_branches(request.user)
        ).first()
        if branch is None:
            raise PermissionDenied("You cannot view stock for this branch.")
        if medicine.pharmacy_id not in (None, branch.pharmacy_id):
            raise NotFound("Medicine not found.")
        raw_quantity = request.query_params.get("quantity")
        quantity = serializers.IntegerField(min_value=1).run_validation(raw_quantity)
        try:
            allocations, _ = FEFOAllocationService.allocate(
                medicine, branch, quantity
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"quantity": exc.messages}) from exc
        return Response(
            {
                "medicine": medicine.pk,
                "branch": branch.pk,
                "requested_quantity": quantity,
                "allocations": [
                    {
                        "batch": MedicineBatchSerializer(item["batch"]).data,
                        "quantity": item["quantity"],
                    }
                    for item in allocations
                ],
            }
        )
