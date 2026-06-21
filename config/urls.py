"""پیکربندی مسیرهای اصلی پروژه."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

# سفارشی‌سازی عنوان‌های پنل مدیریت
admin.site.site_header = "سامانه مدیریت نهار و پذیرایی (وینک)"
admin.site.site_title = "وینک"
admin.site.index_title = "پنل مدیریت"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("people/", include("people.urls")),
    path("guests/", include("guests.urls")),
    path("meals/", include("meals.urls")),
    path("catering/", include("catering.urls")),
    path("reports/", include("reports.urls")),
    path("attendance/", include("attendance.urls")),
    path("", include("dashboard.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
