"""Medicine catalog, dosage forms, manufacturers and inventory batches."""


from datetime import date, timedelta

from django.db import transaction
from django.db.models import Q, QuerySet
from django.db.models import F, IntegerField, OuterRef, Subquery, Sum, Value
from django.db.models.functions import Coalesce
from rest_framework import generics, serializers
from rest_framework.exceptions import PermissionDenied

from apps.accounts.tenancy import accessible_branches, accessible_pharmacies
from apps.transactions.services import record_stock_movement
from .models import (
    BatchStatus,
    DosageForm,
    Manufacturer,
    Medicine,
    MedicineBatch,
    MedicineCategory,
)
from .permissions import CatalogPermission
from .serializers import (
    DosageFormSerializer,
    ManufacturerSerializer,
    MedicineBatchSerializer,
    MedicineSerializer,
    MedicineCategorySerializer,
)


class CategoryListView(generics.ListCreateAPIView):
    """Self-describing catalogue: categories, dosage forms, manufacturers."""

    serializer_class = MedicineCategorySerializer
    permission_classes = [CatalogPermission]

    def get_queryset(self) -> QuerySet:
        qs = MedicineCategory.objects.all()
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active == "true")
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(code__icontains=search))
        ordering = self.request.query_params.get("ordering")
        if ordering in {"name", "-name", "code", "-code", "created_at", "-created_at"}:
            qs = qs.order_by(ordering)
        return qs.select_related("parent")

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=["is_active", "updated_at"])


class CategoryRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """Single category: edit, retire or reactivate."""

    serializer_class = MedicineCategorySerializer
    permission_classes = [CatalogPermission]

    def get_queryset(self) -> QuerySet:
        return MedicineCategory.objects.all()

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=["is_active", "updated_at"])


class MedicineListView(generics.ListCreateAPIView):
    """Medicine catalogue: list with filters, create from existing lookup codes."""

    serializer_class = MedicineSerializer
    permission_classes = [CatalogPermission]

    def get_queryset(self) -> QuerySet:
        pharmacies = accessible_pharmacies(self.request.user)
        qs = Medicine.objects.filter(
            Q(pharmacy__in=pharmacies) | Q(pharmacy__isnull=True)
        )
        category = self.request.query_params.get("category")
        manufacturer = self.request.query_params.get("manufacturer")
        route = self.request.query_params.get("route")
        prescription = self.request.query_params.get("prescription_required")
        is_active = self.request.query_params.get("is_active")
        search = self.request.query_params.get("search")
        if is_active is None:
            qs = qs.filter(is_active=True)
        else:
            qs = qs.filter(is_active=is_active.lower() == "true")
        if category:
            qs = qs.filter(category_id=category)
        if manufacturer:
            qs = qs.filter(manufacturer_id=manufacturer)
        if route:
            qs = qs.filter(route=route)
        if prescription is not None:
            qs = qs.filter(prescription_required=(prescription == "true"))
        if search:
            qs = qs.filter(
                Q(generic_name__icontains=search)
                | Q(brand_name__icontains=search)
                | Q(barcode__icontains=search)
                | Q(gtin__icontains=search)
                | Q(category__name__icontains=search)
                | Q(manufacturer__name__icontains=search)
            )
        pharmacy = self.request.query_params.get("pharmacy")
        if pharmacy:
            if not pharmacies.filter(pk=pharmacy).exists():
                raise PermissionDenied("You cannot view this pharmacy's medicines.")
            qs = qs.filter(pharmacy_id=pharmacy)
        ordering = self.request.query_params.get("ordering")
        if ordering in {
            "generic_name", "-generic_name", "brand_name", "-brand_name",
            "strength", "-strength", "created_at", "-created_at",
        }:
            qs = qs.order_by(ordering)
        return qs.select_related("category", "manufacturer", "dosage_form")

    def perform_create(self, serializer):
        pharmacy = serializer.validated_data.get("pharmacy")
        pharmacies = accessible_pharmacies(self.request.user)
        if pharmacy is None:
            if pharmacies.count() != 1:
                raise serializers.ValidationError(
                    {"pharmacy": "Select one accessible pharmacy to create this medicine."}
                )
            pharmacy = pharmacies.get()
        if not pharmacies.filter(pk=pharmacy.pk).exists():
            raise PermissionDenied("You cannot create medicines for this pharmacy.")
        serializer.save(pharmacy=pharmacy)


class DosageFormListView(generics.ListCreateAPIView):
    """Dosage forms for the catalogue."""

    serializer_class = DosageFormSerializer
    permission_classes = [CatalogPermission]

    def get_queryset(self) -> QuerySet:
        qs = DosageForm.objects.all()
        active = self.request.query_params.get("is_active")
        if active is not None:
            qs = qs.filter(is_active=active == "true")
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(code__icontains=search))
        return qs

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=["is_active", "updated_at"])


class ManufacturerListView(generics.ListCreateAPIView):
    """Manufacturers for the catalogue."""

    serializer_class = ManufacturerSerializer
    permission_classes = [CatalogPermission]

    def get_queryset(self) -> QuerySet:
        qs = Manufacturer.objects.all()
        active = self.request.query_params.get("is_active")
        if active is not None:
            qs = qs.filter(is_active=active == "true")
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(country__icontains=search))
        return qs

    def perform_create(self, serializer):
        serializer.save()

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=["is_active", "updated_at"])


class MedicineRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MedicineSerializer
    permission_classes = [CatalogPermission]

    def get_queryset(self) -> QuerySet:
        return Medicine.objects.filter(
            Q(pharmacy__in=accessible_pharmacies(self.request.user))
            | Q(pharmacy__isnull=True)
        ).select_related(
            "pharmacy", "category", "manufacturer", "dosage_form"
        )

    def perform_update(self, serializer):
        if serializer.instance.pharmacy_id is None and not self.request.user.is_superuser:
            raise PermissionDenied("Shared formulary medicines cannot be edited.")
        serializer.save()

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=["is_active", "updated_at"])


class BatchListView(generics.ListCreateAPIView):
    """Inventory batches (stock on hand per branch). FEFO default ordering.

    Filter by ``?medicine=<id>``, ``?branch=<id>``, ``?status=<status>``.
    """

    serializer_class = MedicineBatchSerializer
    permission_classes = [CatalogPermission]

    def get_queryset(self) -> QuerySet:
        qs = MedicineBatch.objects.filter(
            branch__in=accessible_branches(self.request.user),
        ).filter(
            Q(medicine__pharmacy__in=accessible_pharmacies(self.request.user))
            | Q(medicine__pharmacy__isnull=True)
        )
        medicine = self.request.query_params.get("medicine")
        branch = self.request.query_params.get("branch")
        warehouse = self.request.query_params.get("warehouse")
        category = self.request.query_params.get("category")
        status = self.request.query_params.get("status")
        if medicine:
            qs = qs.filter(medicine_id=medicine)
        if branch:
            qs = qs.filter(branch_id=branch)
        if warehouse:
            qs = qs.filter(warehouse_id=warehouse)
        if category:
            qs = qs.filter(medicine__category_id=category)
        if status:
            if status == "expired":
                qs = qs.filter(expiry_date__lt=date.today())
            elif status == "out_of_stock":
                qs = qs.filter(quantity=0)
            elif status == "expiring":
                qs = qs.filter(
                    quantity__gt=0,
                    expiry_date__gte=date.today(),
                    expiry_date__lte=date.today() + timedelta(days=30),
                )
            else:
                qs = qs.filter(
                    status=status,
                    quantity__gt=0,
                    expiry_date__gte=date.today(),
                )
        if self.request.query_params.get("low_stock") == "true":
            available_batches = MedicineBatch.objects.filter(
                medicine_id=OuterRef("pk"),
                branch__in=accessible_branches(self.request.user),
                quantity__gt=0,
                status=BatchStatus.AVAILABLE,
                expiry_date__gte=date.today(),
            ).values("medicine_id").annotate(
                total=Sum("quantity")
            ).values("total")[:1]
            low_stock_medicines = Medicine.objects.filter(
                Q(pharmacy__in=accessible_pharmacies(self.request.user))
                | Q(pharmacy__isnull=True),
                is_active=True,
            ).annotate(
                available_stock=Coalesce(
                    Subquery(available_batches, output_field=IntegerField()),
                    Value(0),
                )
            ).filter(
                available_stock__lt=F("reorder_level")
            ).values("pk")
            qs = qs.filter(
                medicine_id__in=low_stock_medicines,
                quantity__gt=0,
                status=BatchStatus.AVAILABLE,
                expiry_date__gte=date.today(),
            )
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(
                Q(batch_number__icontains=search)
                | Q(barcode__icontains=search)
                | Q(medicine__generic_name__icontains=search)
                | Q(medicine__brand_name__icontains=search)
            )
        ordering = self.request.query_params.get("ordering")
        if ordering in {
            "expiry_date", "-expiry_date", "quantity", "-quantity",
            "batch_number", "-batch_number",
        }:
            qs = qs.order_by(ordering)
        return qs.select_related(
            "medicine", "medicine__category", "branch", "warehouse"
        )

    @transaction.atomic
    def perform_create(self, serializer):
        branch = serializer.validated_data["branch"]
        if not accessible_branches(self.request.user).filter(pk=branch.pk).exists():
            raise PermissionDenied("You cannot manage inventory for this branch.")
        quantity = serializer.validated_data.get("quantity", 0)
        batch = serializer.save(
            quantity=0,
            status=(
                BatchStatus.EXPIRED
                if serializer.validated_data["expiry_date"] < date.today()
                else BatchStatus.OUT_OF_STOCK
            ),
        )
        if quantity:
            record_stock_movement(
                transaction_type="receipt",
                batch=batch,
                branch=batch.branch,
                warehouse=batch.warehouse,
                quantity=quantity,
                unit_price=batch.purchase_price,
                reference=f"INITIAL-{batch.pk}",
                created_by=self.request.user,
            )

    def perform_update(self, serializer):
        branch = serializer.validated_data.get(
            "branch", serializer.instance.branch
        )
        if not accessible_branches(self.request.user).filter(pk=branch.pk).exists():
            raise PermissionDenied("You cannot manage inventory for this branch.")
        serializer.save()


class BatchRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MedicineBatchSerializer
    permission_classes = [CatalogPermission]

    def get_queryset(self) -> QuerySet:
        return MedicineBatch.objects.filter(
            branch__in=accessible_branches(self.request.user)
        ).filter(
            Q(medicine__pharmacy__in=accessible_pharmacies(self.request.user))
            | Q(medicine__pharmacy__isnull=True)
        ).select_related("medicine", "branch", "warehouse")

    def perform_destroy(self, instance):
        if instance.ledger.exists():
            raise serializers.ValidationError(
                "A batch with inventory history cannot be deleted. Record a stock movement instead."
            )
        instance.delete()


class DosageFormRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """Single dosage form: list, edit, retire or reactivate."""

    serializer_class = DosageFormSerializer
    permission_classes = [CatalogPermission]

    def get_queryset(self) -> QuerySet:
        return DosageForm.objects.all()

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=["is_active", "updated_at"])



class ManufacturerRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """Single manufacturer: list, edit, retire or reactivate."""

    serializer_class = ManufacturerSerializer
    permission_classes = [CatalogPermission]

    def get_queryset(self) -> QuerySet:
        return Manufacturer.objects.all()

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=["is_active", "updated_at"])
