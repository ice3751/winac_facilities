"""ساخت گروه‌های دسترسی برای هر نقش و اتصال مجوزهای مدل به آن‌ها.

این دستور سطح دسترسی کامل را به‌صورت idempotent برقرار می‌کند: برای هر نقش یک Group
با مجوزهای مناسب ساخته و کاربران همان نقش به گروه افزوده می‌شوند. کنترل دسترسی وب
از طریق نقش کاربر و RoleRequiredMixin انجام می‌شود؛ این گروه‌ها همان قواعد را در سطح
مجوزهای استاندارد جنگو (و پنل ادمین) نیز بازتاب می‌دهند.

اجرا:
    python manage.py setup_roles
"""

from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

from accounts.models import User

# برای هر نقش: {app_label: [اکشن‌های مجاز]} — اکشن‌ها از add/change/delete/view
ROLE_PERMISSIONS = {
    User.Roles.RECEPTION: {
        "people": ["add", "change", "view"],
        "guests": ["add", "change", "delete", "view"],
    },
    User.Roles.RESTAURANT: {
        "meals": ["add", "change", "view"],
        "people": ["view"],
        "guests": ["view"],
    },
    User.Roles.PROTOCOL: {
        "catering": ["add", "change", "delete", "view"],
        "people": ["view"],
    },
    User.Roles.HOST: {
        "guests": ["add", "change", "view"],
        "catering": ["add", "change", "view"],
    },
    User.Roles.REPORT_VIEWER: {
        "meals": ["view"],
        "guests": ["view"],
        "people": ["view"],
        "catering": ["view"],
    },
}


def _collect_permissions(app_actions):
    perms = []
    for app_label, actions in app_actions.items():
        for action in actions:
            qs = Permission.objects.filter(
                content_type__app_label=app_label,
                codename__startswith=f"{action}_",
            )
            perms.extend(qs)
    return perms


class Command(BaseCommand):
    help = "ساخت گروه‌های نقش و اتصال مجوزها، و افزودن کاربران به گروه نقش خود"

    def handle(self, *args, **options):
        role_groups = {}
        for role, app_actions in ROLE_PERMISSIONS.items():
            label = dict(User.Roles.choices)[role]
            group, _ = Group.objects.get_or_create(name=f"نقش: {label}")
            group.permissions.set(_collect_permissions(app_actions))
            role_groups[role] = group
            self.stdout.write(f"گروه «{group.name}» با {group.permissions.count()} مجوز آماده شد")

        # افزودن کاربران غیرمدیر به گروه نقش خود
        assigned = 0
        for user in User.objects.filter(is_superuser=False):
            group = role_groups.get(user.role)
            if group:
                user.groups.add(group)
                assigned += 1
        self.stdout.write(self.style.SUCCESS(
            f"تنظیم دسترسی کامل شد. {assigned} کاربر به گروه نقش خود افزوده شدند."
        ))
