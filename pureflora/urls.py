from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [path("django-admin/", admin.site.urls), path("", include("marketplace.urls"))]
handler403 = "marketplace.views.handler403"
handler404 = "marketplace.views.handler404"
handler500 = "marketplace.views.handler500"
# Local development and the short-lived Vercel demo serve uploads from MEDIA_ROOT.
# Vercel's /tmp filesystem is temporary and instance-local; use object storage for
# images that must persist and be shared reliably across all function instances.
if settings.DEBUG or getattr(settings, "ON_VERCEL", False):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
