from django.db.models import QuerySet
from rest_framework import generics, permissions

from .models import Supplier
from .serializers import SupplierSerializer


class SupplierListView(generics.ListCreateAPIView):
    serializer_class = SupplierSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        if self.request.user.is_superuser:
            return Supplier.objects.select_related("pharmacy")
        return (
            Supplier.objects.filter(pharmacy__owner=self.request.user)
            .select_related("pharmacy")
        )

    def perform_create(self, serializer):
        if self.request.user.is_superuser:
            return serializer.save()
        pharmacy_id = self.request.data.get("pharmacy")
        if pharmacy_id not in self.request.user.pharmacies.values_list("pk", flat=True):
            self.permission_denied(self.request)
        serializer.save(pharmacy_id=pharmacy_id)
