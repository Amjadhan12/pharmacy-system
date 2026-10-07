"""Medicine catalog, dosage forms, manufacturers and inventory batches."""


from django.db.models import QuerySet
from rest_framework import generics, permissions

from apps.accounts.tenancy import accessible_branches
from .models import (
    BatchStatus,
    DosageForm,
    Manufacturer,
    Medicine,
    MedicineBatch,
    MedicineCategory,
)
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
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        qs = MedicineCategory.objects.all()
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active == "true")
        return qs.select_related("parent")


class CategoryRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """Single category: edit, retire or reactivate."""

    serializer_class = MedicineCategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        return MedicineCategory.objects.all()


class MedicineListView(generics.ListCreateAPIView):
    """Medicine catalogue: list with filters, create from existing lookup codes."""

    serializer_class = MedicineSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        # Active by default; ``is_active=false`` returns everything.
        qs = Medicine.objects.all()
        category = self.request.query_params.get("category")
        manufacturer = self.request.query_params.get("manufacturer")
        route = self.request.query_params.get("route")
        prescription = self.request.query_params.get("prescription_required")
        if category:
            qs = qs.filter(category_id=category)
        if manufacturer:
            qs = qs.filter(manufacturer_id=manufacturer)
        if route:
            qs = qs.filter(route=route)
        if prescription is not None:
            qs = qs.filter(prescription_required=(prescription == "true"))
        return qs.select_related("category", "manufacturer", "dosage_form")


class DosageFormListView(generics.ListCreateAPIView):
    """Dosage forms for the catalogue."""

    serializer_class = DosageFormSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        return DosageForm.objects.all()


class ManufacturerListView(generics.ListCreateAPIView):
    """Manufacturers for the catalogue."""

    serializer_class = ManufacturerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        return Manufacturer.objects.all()

    def perform_create(self, serializer):
        serializer.save()


class MedicineRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MedicineSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        return Medicine.objects.all().select_related(
            "category", "manufacturer", "dosage_form"
        )


class BatchListView(generics.ListCreateAPIView):
    """Inventory batches (stock on hand per branch). FEFO default ordering.

    Filter by ``?medicine=<id>``, ``?branch=<id>``, ``?status=<status>``.
    """

    serializer_class = MedicineBatchSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        qs = MedicineBatch.objects.filter(
            branch__in=accessible_branches(self.request.user)
        )
        medicine = self.request.query_params.get("medicine")
        branch = self.request.query_params.get("branch")
        status = self.request.query_params.get("status")
        if medicine:
            qs = qs.filter(medicine_id=medicine)
        if branch:
            qs = qs.filter(branch_id=branch)
        if status:
            qs = qs.filter(status=status)
        return qs.select_related("medicine", "branch", "warehouse")

    def perform_create(self, serializer):
        branch = serializer.validated_data["branch"]
        if not accessible_branches(self.request.user).filter(pk=branch.pk).exists():
            self.permission_denied(self.request)
        serializer.save(status=BatchStatus.AVAILABLE)

    def perform_update(self, serializer):
        branch = serializer.validated_data.get(
            "branch", serializer.instance.branch
        )
        if not accessible_branches(self.request.user).filter(pk=branch.pk).exists():
            self.permission_denied(self.request)
        serializer.save()


class BatchRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MedicineBatchSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        return MedicineBatch.objects.filter(
            branch__in=accessible_branches(self.request.user)
        ).select_related("medicine", "branch", "warehouse")


class DosageFormRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """Single dosage form: list, edit, retire or reactivate."""

    serializer_class = DosageFormSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        return DosageForm.objects.all()



class ManufacturerRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """Single manufacturer: list, edit, retire or reactivate."""

    serializer_class = ManufacturerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        return Manufacturer.objects.all()
