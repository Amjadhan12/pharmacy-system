"""Pharmacy (tenant) endpoints."""
from django.db.models import QuerySet
from rest_framework import generics, permissions

from .models import Pharmacy, PharmacyProfile
from .serializers import PharmacySerializer

class PharmacyListView(generics.ListCreateAPIView):
    """List pharmacies owned by the requesting user (all for superusers)."""

    serializer_class = PharmacySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        qs = Pharmacy.objects.all()
        if self.request.user.is_superuser:
            return qs
        return qs.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class PharmacyRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    """Return one pharmacy; only its owner (or a superuser) may view/edit."""

    serializer_class = PharmacySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        return Pharmacy.objects.all().select_related("owner", "profile")

    def get_object(self):
        obj = super().get_object()
        if not (self.request.user.is_superuser or obj.owner == self.request.user):
            self.permission_denied(self.request)
        return obj
