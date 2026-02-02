from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


admin.site.site_header = "Flexofast Helpdesk"
admin.site.site_title = "Flexofast Helpdesk Portal"
admin.site.index_title = "Welcome to Flexofast Helpdesk"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),
    path("tickets/", include("tickets.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
