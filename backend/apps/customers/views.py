from django.db.models import QuerySet
from rest_framework import generics, permissions

from .models import Customer
from .serializers import CustomerSerializer


class CustomerListView(generics.ListCreateAPIView):
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        if self.request.user.is_superuser:
            return Customer.objects.select_related("pharmacy")
        return (
            Customer.objects.filter(pharmacy__owner=self.request.user)
            .select_related("pharmacy")
        )

    def perform_create(self, serializer):
        # Enforce multi-tenant ownership: a customer may only be created in a
        # pharmacy this user owns (or every pharmacy for a superadmin).
        if self.request.user.is_superuser:
            return serializer.save()
        pharmacy_id = self.request.data.get("pharmacy")
        if pharmacy_id not in self.request.user.pharmacies.values_list("pk", flat=True):
            self.permission_denied(self.request)
        serializer.save(pharmacy_id=pharmacy_id)
