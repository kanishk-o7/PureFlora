from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [path("django-admin/", admin.site.urls), path("", include("marketplace.urls"))]
handler403 = "marketplace.views.handler403"
handler404 = "marketplace.views.handler404"
handler500 = "marketplace.views.handler500"
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
