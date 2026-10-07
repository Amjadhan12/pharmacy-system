from django.urls import path

from .views import LedgerAccountListView, JournalEntryListView

app_name = "accounting"

urlpatterns = [
    path("accounts/", LedgerAccountListView.as_view(), name="account-list"),
    path("journals/", JournalEntryListView.as_view(), name="journal-list"),
]
