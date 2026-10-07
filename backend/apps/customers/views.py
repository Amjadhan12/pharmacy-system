from django.db.models import QuerySet
from rest_framework import generics, permissions

from apps.accounts.tenancy import accessible_pharmacies
from .models import Customer
from .serializers import CustomerSerializer


class CustomerListView(generics.ListCreateAPIView):
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        return Customer.objects.filter(
            pharmacy__in=accessible_pharmacies(self.request.user)
        ).select_related("pharmacy")

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
