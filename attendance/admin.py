from django.contrib import admin

from .models import AttendanceDevice, AttendanceEvent


@admin.register(AttendanceDevice)
class AttendanceDeviceAdmin(admin.ModelAdmin):
    list_display = ("device_id", "name", "device_type", "is_active")
    list_filter = ("device_type", "is_active")
    search_fields = ("device_id", "name")


@admin.register(AttendanceEvent)
class AttendanceEventAdmin(admin.ModelAdmin):
    list_display = (
        "occurred_at", "event_type", "card_or_fingerprint", "device", "processing_status",
    )
    list_filter = ("event_type", "processing_status", "device_type")
    search_fields = ("card_or_fingerprint",)
    date_hierarchy = "occurred_at"
    readonly_fields = ("processing_status", "error_message")
