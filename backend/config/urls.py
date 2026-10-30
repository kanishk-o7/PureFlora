from django.urls import include, path
from django.contrib import admin
from django.http import JsonResponse
from rest_framework.routers import DefaultRouter

from catalog.views import ProductViewSet

router = DefaultRouter()
router.register("products", ProductViewSet, basename="product")


def health(request):
    return JsonResponse({"status": "ok", "service": "pureflora-api"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health, name="health"),
    path("api/", include(router.urls)),
]
