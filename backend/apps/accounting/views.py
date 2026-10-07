from decimal import Decimal

from django.db.models import QuerySet
from rest_framework import generics, permissions

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
            qs = qs.filter(pharmacy_id=ph)
        elif not self.request.user.is_superuser:
            qs = qs.filter(pharmacy__owner=self.request.user)
        return qs.select_related("pharmacy", "parent")

    def perform_create(self, serializer):
        if not self.request.user.is_superuser:
            self.permission_denied(self.request)
        serializer.save()
