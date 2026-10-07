"""Branch and warehouse endpoints."""

from django.urls import path

from .views import (
    BranchListView,
    BranchRetrieveUpdateDestroyView,
    WarehouseListView,
    WarehouseRetrieveUpdateDestroyView,
)

app_name = "branches"

urlpatterns = [
    path("", BranchListView.as_view(), name="list"),
    path("<int:pk>/", BranchRetrieveUpdateDestroyView.as_view(), name="detail"),
    path("warehouses/", WarehouseListView.as_view(), name="warehouse-list"),
    path("warehouses/<int:pk>/", WarehouseRetrieveUpdateDestroyView.as_view(), name="warehouse-detail"),
]
