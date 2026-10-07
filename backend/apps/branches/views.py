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
