from django.contrib import admin

from .models import (
    CateringItem,
    CateringLocation,
    CateringRequest,
    CateringRequestItem,
)


@admin.register(CateringItem)
class CateringItemAdmin(admin.ModelAdmin):
    list_display = ("name", "unit", "is_active")
    list_filter = ("unit", "is_active")
    search_fields = ("name",)


@admin.register(CateringLocation)
class CateringLocationAdmin(admin.ModelAdmin):
    list_display = ("name", "capacity", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


class CateringRequestItemInline(admin.TabularInline):
    model = CateringRequestItem
    extra = 1
    autocomplete_fields = ("item",)


@admin.register(CateringRequest)
class CateringRequestAdmin(admin.ModelAdmin):
    list_display = (
        "title", "host", "catering_date", "location", "start_time", "end_time",
        "occasion", "headcount", "status",
    )
    list_filter = ("status", "occasion", "catering_date", "location")
    search_fields = ("title",)
    autocomplete_fields = ("host", "location")
    date_hierarchy = "catering_date"
    inlines = [CateringRequestItemInline]


@admin.register(CateringRequestItem)
class CateringRequestItemAdmin(admin.ModelAdmin):
    list_display = (
        "item", "request", "quantity", "needs_purchase", "purchase_status",
        "purchased_by", "purchased_at",
    )
    list_filter = ("needs_purchase", "purchase_status")
    search_fields = ("item__name", "request__title")
    autocomplete_fields = ("item", "request", "purchased_by")
