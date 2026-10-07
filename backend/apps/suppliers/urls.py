from django.urls import path

from .views import SupplierDetailView, SupplierListView

app_name = "suppliers"

urlpatterns = [
    path("", SupplierListView.as_view(), name="list"),
    path("<int:pk>/", SupplierDetailView.as_view(), name="detail"),
]
