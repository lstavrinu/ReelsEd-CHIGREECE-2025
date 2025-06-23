from django.conf import settings
from django.conf.urls import include
from django.conf.urls.static import static
from django.urls import re_path

urlpatterns = [
    re_path(r'^web_app/', include('web_app.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
