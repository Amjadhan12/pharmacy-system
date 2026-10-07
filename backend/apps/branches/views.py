"""Branch and warehouse endpoints."""

from django.db.models import QuerySet
from rest_framework import generics, permissions

from .models import Branch, Warehouse
from .serializers import BranchSerializer, WarehouseSerializer


class BranchListView(generics.ListCreateAPIView):
    """List branches of the requesting user's pharmacies (all staff see the catalog)."""

    serializer_class = BranchSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        return Branch.objects.all().select_related("pharmacy", "manager")

    def perform_create(self, serializer):
        pharmacy_id = self.request.data.get("pharmacy")
        # A staff member may only create branches inside their own pharmacies.
        if not (self.request.user.is_superuser and pharmacy_id):
            pharmacy_ids = self.request.user.pharmacies.values_list("pk", flat=True)
            if pharmacy_id and pharmacy_id not in pharmacy_ids:
                self.permission_denied(self.request)
        serializer.save()


class BranchRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """Return / edit / delete a single branch."""

    serializer_class = BranchSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        return Branch.objects.all().select_related("pharmacy", "manager")

    def perform_destroy(self, instance):
        # Keep branch records while still allowing hard delete by admin.
        if not self.request.user.is_superuser:
            self.permission_denied(self.request)
        super().perform_destroy(instance)


class WarehouseListView(generics.ListCreateAPIView):
    """List and create warehouses for the requesting user's branches."""

    serializer_class = WarehouseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        qs = Warehouse.objects.select_related("branch", "branch__pharmacy")
        branch = self.request.query_params.get("branch")
        if branch:
            qs = qs.filter(branch_id=branch)
        return qs

    def perform_create(self, serializer):
        branch = serializer.validated_data.get("branch")
        if branch and self.request.user.is_superuser:
            serializer.save()
            return
        allowed_branch_ids = set(
            self.request.user.pharmacies.values_list("branches__id", flat=True)
        )
        if branch and branch.id in allowed_branch_ids:
            serializer.save()
            return
        self.permission_denied(self.request)


class WarehouseRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """Return / edit / delete a specific warehouse."""

    serializer_class = WarehouseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        return Warehouse.objects.select_related("branch", "branch__pharmacy")

    def get_object(self):
        obj = super().get_object()
        if self.request.user.is_superuser:
            return obj
        allowed_branch_ids = set(
            self.request.user.pharmacies.values_list("branches__id", flat=True)
        )
        if obj.branch_id in allowed_branch_ids:
            return obj
        self.permission_denied(self.request)

