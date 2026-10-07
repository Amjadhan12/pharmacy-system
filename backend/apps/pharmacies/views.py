"""Pharmacy (tenant) endpoints."""
from django.db.models import QuerySet
from rest_framework import generics, permissions

from apps.accounts.tenancy import accessible_pharmacies
from .models import Pharmacy, PharmacyProfile
from .serializers import PharmacySerializer

class PharmacyListView(generics.ListCreateAPIView):
    """List pharmacies owned by the requesting user (all for superusers)."""

    serializer_class = PharmacySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        return accessible_pharmacies(self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class PharmacyRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    """Return one pharmacy; only its owner (or a superuser) may view/edit."""

    serializer_class = PharmacySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        return accessible_pharmacies(self.request.user).select_related(
            "owner", "profile"
        )

    def perform_update(self, serializer):
        pharmacy = serializer.instance
        if not (
            self.request.user.is_superuser
            or pharmacy.owner_id == self.request.user.pk
        ):
            self.permission_denied(self.request)
        serializer.save()
