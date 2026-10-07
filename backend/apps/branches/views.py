"""Branch and warehouse endpoints."""

from django.db.models import QuerySet
from rest_framework import generics, permissions

from apps.accounts.tenancy import accessible_branches, accessible_pharmacies
from .models import Branch, Warehouse
from .serializers import BranchSerializer, WarehouseSerializer


class BranchListView(generics.ListCreateAPIView):
    """List branches of the requesting user's pharmacies (all staff see the catalog)."""

    serializer_class = BranchSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        return accessible_branches(self.request.user).select_related(
            "pharmacy", "manager"
        )

    def perform_create(self, serializer):
        pharmacy = serializer.validated_data["pharmacy"]
        if not (
            self.request.user.is_superuser
            or pharmacy.owner_id == self.request.user.pk
        ):
            self.permission_denied(self.request)
        serializer.save()

    def perform_update(self, serializer):
        pharmacy = serializer.validated_data.get(
            "pharmacy", serializer.instance.pharmacy
        )
        if not (
            self.request.user.is_superuser
            or pharmacy.owner_id == self.request.user.pk
        ):
            self.permission_denied(self.request)
        serializer.save()


class BranchRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """Return / edit / delete a single branch."""

    serializer_class = BranchSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        return accessible_branches(self.request.user).select_related(
            "pharmacy", "manager"
        )

    def perform_update(self, serializer):
        pharmacy = serializer.validated_data.get(
            "pharmacy", serializer.instance.pharmacy
        )
        if not (
            self.request.user.is_superuser
            or pharmacy.owner_id == self.request.user.pk
        ):
            self.permission_denied(self.request)
        serializer.save()

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
        qs = Warehouse.objects.filter(
            branch__in=accessible_branches(self.request.user)
        ).select_related("branch", "branch__pharmacy")
        branch = self.request.query_params.get("branch")
        if branch:
            qs = qs.filter(branch_id=branch)
        return qs

    def perform_create(self, serializer):
        branch = serializer.validated_data.get("branch")
        if branch is None or not (
            self.request.user.is_superuser
            or branch.pharmacy.owner_id == self.request.user.pk
        ):
            self.permission_denied(self.request)
        serializer.save()


class WarehouseRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """Return / edit / delete a specific warehouse."""

    serializer_class = WarehouseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        return Warehouse.objects.filter(
            branch__in=accessible_branches(self.request.user)
        ).select_related("branch", "branch__pharmacy")

    def perform_update(self, serializer):
        branch = serializer.validated_data.get("branch", serializer.instance.branch)
        if not (
            self.request.user.is_superuser
            or branch.pharmacy.owner_id == self.request.user.pk
        ):
            self.permission_denied(self.request)
        serializer.save()
