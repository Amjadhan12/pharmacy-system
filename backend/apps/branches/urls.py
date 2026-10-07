"""Branch and warehouse endpoints."""

from django.urls import path

from .views import BranchListView, BranchRetrieveUpdateDestroyView

app_name = "branches"

urlpatterns = [
    path("", BranchListView.as_view(), name="list"),
    path("<int:pk>/", BranchRetrieveUpdateDestroyView.as_view(), name="detail"),
]
