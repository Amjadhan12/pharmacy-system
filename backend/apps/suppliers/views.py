from django.db.models import QuerySet
from rest_framework import generics, permissions

from apps.accounts.tenancy import accessible_pharmacies
from .models import Supplier
from .serializers import SupplierSerializer


class SupplierListView(generics.ListCreateAPIView):
    serializer_class = SupplierSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        return Supplier.objects.filter(
            pharmacy__in=accessible_pharmacies(self.request.user)
        ).select_related("pharmacy")

    def perform_create(self, serializer):
        pharmacy_id = self.request.data.get("pharmacy")
        if not (
            self.request.user.is_superuser
            or self.request.user.pharmacies.filter(pk=pharmacy_id).exists()
        ):
            self.permission_denied(self.request)
        serializer.save(pharmacy_id=pharmacy_id)
