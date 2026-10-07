"""Medicine catalog, categories, dosage forms and batches."""

from django.urls import path

from .views import (
    BatchListView,
    BatchRetrieveUpdateDestroyView,
    CategoryListView,
    CategoryRetrieveUpdateDestroyView,
    DosageFormListView,
    DosageFormRetrieveUpdateDestroyView,
    ManufacturerListView,
    ManufacturerRetrieveUpdateDestroyView,
    MedicineListView,
    MedicineRetrieveUpdateDestroyView,
)

app_name = "medicines"

urlpatterns = [
    # Catalog
    path("categories/", CategoryListView.as_view(), name="category-list"),
    path("categories/<int:pk>/", CategoryRetrieveUpdateDestroyView.as_view(), name="category-detail"),
    path("dosage-forms/", DosageFormListView.as_view(), name="dosageform-list"),
    path("dosage-forms/<int:pk>/", DosageFormRetrieveUpdateDestroyView.as_view(), name="dosageform-detail"),
    path("manufacturers/", ManufacturerListView.as_view(), name="manufacturer-list"),
    path("manufacturers/<int:pk>/", ManufacturerRetrieveUpdateDestroyView.as_view(), name="manufacturer-detail"),
    path("medicines/", MedicineListView.as_view(), name="medicine-list"),
    path("medicines/<int:pk>/", MedicineRetrieveUpdateDestroyView.as_view(), name="medicine-detail"),
    # Inventory batches (per branch)
    path("batches/", BatchListView.as_view(), name="batch-list"),
    path("batches/<int:pk>/", BatchRetrieveUpdateDestroyView.as_view(), name="batch-detail"),
]
