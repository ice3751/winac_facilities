from django.urls import path

from . import api

app_name = "attendance"

urlpatterns = [
    # API داخلی دریافت رویداد دستگاه تردد (فاز ۵)
    path("api/events/", api.ingest_event, name="ingest_event"),
]
