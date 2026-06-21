from django.contrib import admin

from .models import DailyMealPlan, DuplicateAttempt, MealToken


@admin.register(MealToken)
class MealTokenAdmin(admin.ModelAdmin):
    list_display = (
        "token_code", "date", "recipient_type", "recipient_name",
        "status", "issued_at", "consumed_at",
    )
    list_filter = ("status", "recipient_type", "date")
    search_fields = (
        "token_code", "personnel__first_name", "personnel__last_name",
        "guest__first_name", "guest__last_name",
    )
    autocomplete_fields = ("personnel", "guest", "issued_by", "consumed_by")
    date_hierarchy = "date"
    readonly_fields = ("issued_at", "consumed_at")


@admin.register(DailyMealPlan)
class DailyMealPlanAdmin(admin.ModelAdmin):
    list_display = (
        "date", "expected_personnel", "expected_guests", "total_ordered",
    )
    date_hierarchy = "date"


@admin.register(DuplicateAttempt)
class DuplicateAttemptAdmin(admin.ModelAdmin):
    list_display = ("created_at", "kind", "recipient_label", "message")
    list_filter = ("kind", "date")
    search_fields = ("recipient_label", "message")
    date_hierarchy = "date"
