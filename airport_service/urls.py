from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView
)


urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "api/airport/",
        include("airport.urls", namespace="airport"),
    ),
    path(
        "api/user/",
        include("user.urls", namespace="user"),
    ),
   path(
       "api/doc/",
       SpectacularAPIView.as_view(),
       name="schema"
   ),
   path(
       "api/docs/",
       SpectacularSwaggerView.as_view(url_name="schema"),
       name="swagger-ui"
   ),
   path(
       "api/docs/redoc/",
       SpectacularRedocView.as_view(url_name="schema"),
       name="redoc"
   ),

]

if settings.DEBUG:
    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
    ]

    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
