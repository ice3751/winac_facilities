"""پردازش دسته‌ای رویدادهای تردد پردازش‌نشده.

اجرا (مثلاً به‌صورت زمان‌بندی‌شده/کرون در فاز اتصال دستگاه):
    python manage.py process_attendance_events
"""

from django.core.management.base import BaseCommand

from attendance.services import process_pending


class Command(BaseCommand):
    help = "پردازش رویدادهای تردد پردازش‌نشده و صدور ژتون در صورت نیاز"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=None,
                            help="حداکثر تعداد رویداد برای پردازش")

    def handle(self, *args, **options):
        count = process_pending(limit=options.get("limit"))
        self.stdout.write(self.style.SUCCESS(f"{count} رویداد پردازش شد."))
