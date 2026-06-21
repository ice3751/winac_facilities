from django.contrib import admin

from .models import CardAssignment, Guest, GuestCard


@admin.register(Guest)
class GuestAdmin(admin.ModelAdmin):
    list_display = (
        "full_name", "company", "guest_type", "host_personnel",
        "visit_date", "needs_lunch", "approval_status", "status",
    )
    list_filter = ("approval_status", "guest_type", "status", "needs_lunch",
                   "needs_catering", "visit_date")
    search_fields = ("first_name", "last_name", "company", "phone")
    autocomplete_fields = ("host_personnel", "approved_by")
    readonly_fields = ("approved_by", "approved_at")
    date_hierarchy = "visit_date"


@admin.register(GuestCard)
class GuestCardAdmin(admin.ModelAdmin):
    list_display = ("title", "card_code", "status")
    list_filter = ("status",)
    search_fields = ("title", "card_code")


@admin.register(CardAssignment)
class CardAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "card", "guest", "assigned_date", "delivered_at", "returned_at", "status",
    )
    list_filter = ("status", "assigned_date")
    search_fields = ("guest__first_name", "guest__last_name", "card__card_code")
    autocomplete_fields = ("guest", "card", "delivered_by")
    date_hierarchy = "assigned_date"
