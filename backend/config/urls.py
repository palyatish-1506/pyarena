"""Root URL configuration.

/api/v1/  -> versioned REST API
/api/docs/ -> drf-spectacular Swagger UI (interactive API explorer)
/admin/   -> Django admin
"""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from config.views import health

api_v1_patterns = [
    path("health/", health, name="health"),
    path("me/", include("accounts.me_urls")),
    path("leaderboard/", include("leaderboard.urls")),
    path("live/", include("livequiz.urls")),
    path("problems/", include("codepractice.urls")),
    path("", include("community.urls")),
    path("auth/", include("accounts.urls")),
    path("admin/", include("accounts.admin_urls")),
    path("questions/", include("questions.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include(api_v1_patterns)),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]
