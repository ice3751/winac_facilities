from django.contrib import admin

from .models import Personnel


@admin.register(Personnel)
class PersonnelAdmin(admin.ModelAdmin):
    list_display = (
        "personnel_code", "full_name", "org_unit", "person_type", "is_active", "card_id",
    )
    list_filter = ("person_type", "is_active", "org_unit")
    search_fields = ("first_name", "last_name", "personnel_code", "card_id")
    list_per_page = 50
