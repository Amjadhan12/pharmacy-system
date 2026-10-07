from decimal import Decimal

from django.db.models import QuerySet
from rest_framework import generics, permissions

from apps.accounts.tenancy import accessible_pharmacies
from apps.pharmacies.models import Pharmacy
from .models import JournalEntry, LedgerAccount
from .serializers import (
    JournalEntrySerializer,
    LedgerAccountSerializer,
)


class LedgerAccountListView(generics.ListCreateAPIView):
    serializer_class = LedgerAccountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        ph = self.request.query_params.get("pharmacy")
        qs = LedgerAccount.objects.filter(is_active=True)
        if ph:
            qs = qs.filter(
                pharmacy_id=ph,
                pharmacy__in=accessible_pharmacies(self.request.user),
            )
        else:
            qs = qs.filter(
                pharmacy__in=accessible_pharmacies(self.request.user)
            )
        return qs.select_related("pharmacy", "parent")

    def perform_create(self, serializer):
        if not self.request.user.is_superuser:
            self.permission_denied(self.request)
        serializer.save()


class JournalEntryListView(generics.ListAPIView):
    serializer_class = JournalEntrySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        pharmacies = accessible_pharmacies(self.request.user)
        qs = JournalEntry.objects.filter(
            lines__account__pharmacy__in=pharmacies
        ).distinct()
        pharmacy_id = self.request.query_params.get("pharmacy")
        if pharmacy_id:
            qs = qs.filter(lines__account__pharmacy_id=pharmacy_id)
        return qs.prefetch_related("lines__account").select_related("created_by")
