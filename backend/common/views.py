"""Shared API views."""
import logging
from datetime import timedelta

from django.db import connection
from django.db.models import Sum
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.tenancy import accessible_branches, accessible_pharmacies
from apps.customers.models import Customer
from apps.medicines.models import Medicine, MedicineBatch
from apps.suppliers.models import Supplier

logger = logging.getLogger("pharmafin")


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """Liveness/readiness probe used by the frontend, mobile and ops tooling."""
    database = "ok"
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:  # pragma: no cover - only on DB outage
        database = "unavailable"
        logger.exception("Health check: database unavailable")

    healthy = database == "ok"
    return Response(
        {
            "success": healthy,
            "message": "" if healthy else "Database unavailable.",
            "data": {
                "service": "pharmafin-api",
                "status": "ok" if healthy else "degraded",
                "database": database,
                "time": timezone.now().isoformat(),
            },
        }
    )


class DashboardSummaryView(APIView):
    """Return dashboard counts calculated from the user's accessible records."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        pharmacies = accessible_pharmacies(request.user)
        branches = accessible_branches(request.user)
        batches = MedicineBatch.objects.filter(branch__in=branches)
        today = timezone.localdate()

        return Response(
            {
                "pharmacies": pharmacies.count(),
                "branches": branches.count(),
                "medicines": Medicine.objects.filter(is_active=True).count(),
                "batches": batches.count(),
                "stock_units": batches.aggregate(total=Sum("quantity"))["total"] or 0,
                "expired_batches": batches.filter(expiry_date__lt=today).count(),
                "expiring_batches": batches.filter(
                    expiry_date__gte=today,
                    expiry_date__lte=today + timedelta(days=90),
                ).count(),
                "suppliers": Supplier.objects.filter(pharmacy__in=pharmacies).count(),
                "customers": Customer.objects.filter(pharmacy__in=pharmacies).count(),
            }
        )
