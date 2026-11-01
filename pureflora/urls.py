from django.contrib import admin
from django.urls import include, path
from django.urls import re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

urlpatterns = [path("django-admin/", admin.site.urls), path("", include("marketplace.urls"))]
handler403 = "marketplace.views.handler403"
handler404 = "marketplace.views.handler404"
handler500 = "marketplace.views.handler500"
# Django's static() helper returns no media route when DEBUG=False. Add an
# explicit route for the temporary Vercel demo; persistent object storage is
# needed for reliable media across function instances and restarts.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
elif getattr(settings, "ON_VERCEL", False):
    urlpatterns += [
        re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
    ]
