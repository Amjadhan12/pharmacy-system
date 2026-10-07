from django.urls import path

from .views import InventoryTransactionListView, StockMovementView

app_name = "transactions"

urlpatterns = [
    path("", InventoryTransactionListView.as_view(), name="list"),
    path(
        "stock/<str:transaction_type>/",
        StockMovementView.as_view(),
        name="stock-movement",
    ),
]
