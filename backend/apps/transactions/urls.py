from django.urls import path

from .views import InventoryTransactionListView

app_name = "transactions"

urlpatterns = [
    path("", InventoryTransactionListView.as_view(), name="list"),
]
