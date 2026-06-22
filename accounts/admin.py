from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "display_name", "role", "org_unit", "is_active", "is_staff")
    list_filter = ("role", "org_unit", "is_active", "is_staff", "is_superuser")
    search_fields = ("username", "full_name_fa", "org_unit", "first_name", "last_name", "email")

    fieldsets = DjangoUserAdmin.fieldsets + (
        ("اطلاعات سازمانی", {"fields": ("role", "org_unit", "full_name_fa")}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ("اطلاعات سازمانی", {"fields": ("role", "org_unit", "full_name_fa")}),
    )
