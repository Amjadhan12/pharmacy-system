from django.db.models import Q, QuerySet
from rest_framework import generics, permissions

from apps.accounts.tenancy import accessible_pharmacies
from .models import Customer
from .serializers import CustomerSerializer


class CustomerListView(generics.ListCreateAPIView):
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        qs = Customer.objects.filter(
            pharmacy__in=accessible_pharmacies(self.request.user)
        )
        is_active = self.request.query_params.get("is_active")
        qs = qs.filter(is_active=is_active.lower() == "true") if is_active else qs.filter(is_active=True)
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(
                Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(email__icontains=search)
                | Q(phone__icontains=search)
            )
        return qs.select_related("pharmacy")

    def perform_create(self, serializer):
        # Enforce multi-tenant ownership: a customer may only be created in a
        # pharmacy this user owns (or every pharmacy for a superadmin).
        pharmacy_id = self.request.data.get("pharmacy")
        if not (
            self.request.user.is_superuser
            or self.request.user.pharmacies.filter(pk=pharmacy_id).exists()
        ):
            self.permission_denied(self.request)
        serializer.save(pharmacy_id=pharmacy_id)


class CustomerDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        return Customer.objects.filter(
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
