from django.contrib import admin

from .models import CateringItem, CateringRequest, CateringRequestItem


@admin.register(CateringItem)
class CateringItemAdmin(admin.ModelAdmin):
    list_display = ("name", "unit", "is_active")
    list_filter = ("unit", "is_active")
    search_fields = ("name",)


class CateringRequestItemInline(admin.TabularInline):
    model = CateringRequestItem
    extra = 1
    autocomplete_fields = ("item",)


@admin.register(CateringRequest)
class CateringRequestAdmin(admin.ModelAdmin):
    list_display = (
        "title", "host", "catering_date", "occasion", "headcount", "status",
    )
    list_filter = ("status", "occasion", "catering_date")
    search_fields = ("title", "location")
    autocomplete_fields = ("host",)
    date_hierarchy = "catering_date"
    inlines = [CateringRequestItemInline]
