"""Tenant access derived from pharmacy ownership and explicit branch assignments."""

from django.db.models import Q, QuerySet

from apps.branches.models import Branch
from apps.pharmacies.models import Pharmacy


def accessible_pharmacies(user) -> QuerySet[Pharmacy]:
    pharmacies = Pharmacy.objects.all()
    if not user.is_authenticated:
        return pharmacies.none()
    if user.is_superuser:
        return pharmacies
    return pharmacies.filter(
        Q(owner_id=user.pk) | Q(branches__user_branches__user_id=user.pk)
    ).distinct()


def accessible_branches(user) -> QuerySet[Branch]:
    branches = Branch.objects.all()
    if not user.is_authenticated:
        return branches.none()
    if user.is_superuser:
        return branches
    return branches.filter(
        Q(pharmacy__owner_id=user.pk) | Q(user_branches__user_id=user.pk)
    ).distinct()
