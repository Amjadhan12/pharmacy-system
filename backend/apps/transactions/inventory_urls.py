from django.urls import path

from apps.medicines.views import BatchListView, BatchRetrieveUpdateDestroyView
from .inventory_views import BatchExpiryListView, FEFOAvailabilityView, LowStockListView
from .views import InventoryTransactionListView, StockMovementView, StockTransferView

app_name = "inventory"

urlpatterns = [
    path("", BatchListView.as_view(), name="batch-list"),
    path("<int:pk>/", BatchRetrieveUpdateDestroyView.as_view(), name="batch-detail"),
    path("transactions/", InventoryTransactionListView.as_view(), name="transactions"),
    path("transfers/", StockTransferView.as_view(), name="transfer"),
    path(
        "transactions/stock/<str:transaction_type>/",
        StockMovementView.as_view(),
        name="stock-movement",
    ),
    path("low-stock/", LowStockListView.as_view(), name="low-stock"),
    path("expiring/", BatchExpiryListView.as_view(), name="expiring"),
    path("expired/", BatchExpiryListView.as_view(), name="expired"),
    path("fefo/<int:medicine_id>/", FEFOAvailabilityView.as_view(), name="fefo"),
]
