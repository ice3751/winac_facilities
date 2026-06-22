"""ساخت یک کاربر «میزبان» برای هر واحد سازمانی.

اجرا:
    python manage.py create_unit_hosts

این دستور idempotent است؛ اجرای مجدد کاربرهای تکراری نمی‌سازد و فقط واحدهای جدید را
اضافه می‌کند. رمز اولیهٔ همهٔ کاربرها ``host12345`` است که باید پس از اولین ورود
تغییر داده شود.
"""

from django.core.management.base import BaseCommand

from accounts.models import User

DEFAULT_PASSWORD = "host12345"

# (نام کاربری, واحد سازمانی)
UNIT_HOSTS = [
    ("host_eng", "فنی مهندسی"),
    ("host_finance", "مالی"),
    ("host_edari", "اداری"),
    ("host_it", "فناوری اطلاعات"),
    ("host_secretary", "منشی دفتر مدیریت"),
    ("host_tamin", "تامین"),
    ("host_logistics", "برنامه ریزی و لجستیک"),
]


class Command(BaseCommand):
    help = "ساخت کاربر میزبان (نقش host) برای هر واحد سازمانی"

    def handle(self, *args, **options):
        created = 0
        for username, unit in UNIT_HOSTS:
            user, was_created = User.objects.get_or_create(
                username=username,
                defaults={
                    "role": User.Roles.HOST,
                    "org_unit": unit,
                    "full_name_fa": f"میزبان واحد {unit}",
                    "is_staff": False,
                    "is_active": True,
                },
            )
            if was_created:
                user.set_password(DEFAULT_PASSWORD)
                user.save()
                created += 1
                self.stdout.write(f"  ساخته شد: {username}  →  {unit}")
            else:
                # واحد را در صورت خالی‌بودن تکمیل کن (برای کاربرهای قدیمی)
                if not user.org_unit:
                    user.org_unit = unit
                    user.save(update_fields=["org_unit"])
                self.stdout.write(f"  از قبل موجود: {username}  ({unit})")

        self.stdout.write(self.style.SUCCESS(
            f"انجام شد. {created} کاربر میزبان جدید ساخته شد. رمز اولیه: {DEFAULT_PASSWORD}"
        ))
