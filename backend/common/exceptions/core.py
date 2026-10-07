"""Consistent API error handling for PharmaFin.

All errors are returned as:
    {"success": false, "message": "...", "errors": {...}}

Stack traces are never exposed to API clients.
"""
import logging

from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger("pharmafin")


def _envelope(message: str, errors: dict) -> dict:
    return {"success": False, "message": message, "errors": errors}


def api_exception_handler(exc, context):
    """DRF exception handler producing the standard error envelope."""
    if isinstance(exc, ValidationError):
        if hasattr(exc, "message_dict"):
            errors = exc.message_dict
        else:
            errors = {"non_field_errors": list(exc.messages)}
        return Response(
            _envelope("Validation failed.", errors),
            status=status.HTTP_400_BAD_REQUEST,
        )

    if isinstance(exc, Http404):
        return Response(
            _envelope("The requested resource was not found.", {}),
            status=status.HTTP_404_NOT_FOUND,
        )

    if isinstance(exc, PermissionDenied):
        return Response(
            _envelope("You do not have permission to perform this action.", {}),
            status=status.HTTP_403_FORBIDDEN,
        )

    response = drf_exception_handler(exc, context)

    if response is None:
        logger.exception("Unhandled API exception: %s", exc, exc_info=True)
        return Response(
            _envelope(
                "An unexpected error occurred. Please try again later.",
                {},
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    detail = getattr(exc, "detail", None)
    if isinstance(detail, dict):
        errors = detail
        message = (
            "Validation failed."
            if response.status_code == status.HTTP_400_BAD_REQUEST
            else "Request failed."
        )
    elif isinstance(detail, (list, tuple)):
        errors = {"detail": [str(item) for item in detail]}
        message = " ".join(str(item) for item in detail) or "Request failed."
    else:
        message = str(detail) if detail else "Request failed."
        errors = {"detail": message} if detail else {}

    return Response(
        _envelope(message, errors),
        status=response.status_code,
    )
