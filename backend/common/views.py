"""Shared API views."""
import logging

from django.db import connection
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

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
