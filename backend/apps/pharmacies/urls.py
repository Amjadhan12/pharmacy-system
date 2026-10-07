"""Pharmacy (tenant) endpoints."""

from django.urls import path

from .views import PharmacyListView, PharmacyRetrieveUpdateView

app_name = "pharmacies"

urlpatterns = [
    path("", PharmacyListView.as_view(), name="list"),
    path("<int:pk>/", PharmacyRetrieveUpdateView.as_view(), name="detail"),
]
