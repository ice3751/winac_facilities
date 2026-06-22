"""context processor مشترک برای دسترسی به اطلاعات کلی و منوی نقش‌محور."""

from .utils import jalali_today_str


def app_context(request):
    perms_nav = {"people": False, "guests": False, "meals": False,
                 "catering": False, "reports": False, "guest_approvals": False,
                 "catering_approvals": False, "approvals": False,
                 "catering_manage": False, "supply": False}

    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        R = user.Roles
        admin = user.is_admin_role
        is_office = admin or user.role == R.OFFICE_MANAGER
        perms_nav = {
            "people": admin or user.role in {R.RECEPTION, R.RESTAURANT, R.HOST},
            "guests": admin or user.role in {R.RECEPTION, R.HOST},
            "meals": admin or user.role in {R.RESTAURANT, R.RECEPTION},
            "catering": admin or user.role in {R.PROTOCOL, R.HOST},
            "reports": admin or user.role == R.REPORT_VIEWER,
            "guest_approvals": is_office,
            "catering_approvals": is_office,
            "approvals": is_office,
            "catering_manage": admin or user.role == R.PROTOCOL,
            "supply": admin or user.role == R.SUPPLY,
        }

    return {
        "APP_NAME": "سامانه مدیریت نهار و پذیرایی",
        "APP_SHORT_NAME": "ویناک",
        "TODAY_JALALI": jalali_today_str(with_month_name=True),
        "perms_nav": perms_nav,
    }
