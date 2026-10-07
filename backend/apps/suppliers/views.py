from django.db.models import Q, QuerySet
from rest_framework import generics, permissions

from apps.accounts.tenancy import accessible_pharmacies
from .models import Supplier
from .serializers import SupplierSerializer


class SupplierListView(generics.ListCreateAPIView):
    serializer_class = SupplierSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        qs = Supplier.objects.filter(
            pharmacy__in=accessible_pharmacies(self.request.user)
        )
        is_active = self.request.query_params.get("is_active")
        qs = qs.filter(is_active=is_active.lower() == "true") if is_active else qs.filter(is_active=True)
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(
                Q(name__icontains=search)
                | Q(legal_name__icontains=search)
                | Q(email__icontains=search)
                | Q(phone__icontains=search)
            )
        return qs.select_related("pharmacy")

    def perform_create(self, serializer):
        pharmacy_id = self.request.data.get("pharmacy")
        if not (
            self.request.user.is_superuser
            or self.request.user.pharmacies.filter(pk=pharmacy_id).exists()
        ):
            self.permission_denied(self.request)
        serializer.save(pharmacy_id=pharmacy_id)


class SupplierDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SupplierSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        return Supplier.objects.filter(
            pharmacy__in=accessible_pharmacies(self.request.user)
        ).select_related("pharmacy")

    def perform_update(self, serializer):
        pharmacy = serializer.validated_data.get(
            "pharmacy", serializer.instance.pharmacy
        )
        if not accessible_pharmacies(self.request.user).filter(pk=pharmacy.pk).exists():
            self.permission_denied(self.request)
        serializer.save()

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=["is_active", "updated_at"])
