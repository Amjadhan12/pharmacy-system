"""Root URL configuration for PharmaFin."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from common.views import health_check

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/health/", health_check, name="health-check"),
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/pharmacies/", include("apps.pharmacies.urls")),
    path("api/v1/branches/", include("apps.branches.urls")),
    path("api/v1/medicines/", include("apps.medicines.urls")),
]

if settings.DEBUG:  # pragma: no cover
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
