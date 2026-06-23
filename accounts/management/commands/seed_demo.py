"""ساخت کاربران نمونه برای هر نقش و مقداری دادهٔ آزمایشی برای شروع سریع.

اجرا:
    python manage.py seed_demo

این دستور idempotent است؛ اجرای مجدد دادهٔ تکراری نمی‌سازد.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import User
from catering.models import CateringItem, CateringLocation
from guests.models import Guest, GuestCard
from people.models import Personnel


class Command(BaseCommand):
    help = "ساخت کاربران نمونه برای هر نقش و دادهٔ آزمایشی اولیه"

    def handle(self, *args, **options):
        # کاربر مدیر سیستم (superuser)
        admin, created = User.objects.get_or_create(
            username="admin",
            defaults={"role": User.Roles.ADMIN, "full_name_fa": "مدیر سیستم",
                      "is_staff": True, "is_superuser": True},
        )
        if created:
            admin.set_password("admin12345")
            admin.save()
            self.stdout.write(self.style.SUCCESS("کاربر admin ساخته شد (رمز: admin12345)"))

        # کاربر نمونه برای هر نقش
        role_users = {
            "reception": (User.Roles.RECEPTION, "کاربر پذیرش"),
            "restaurant": (User.Roles.RESTAURANT, "مسئول رستوران"),
            "protocol": (User.Roles.PROTOCOL, "واحد تشریفات"),
            "host": (User.Roles.HOST, "مدیر واحد / میزبان"),
            "office": (User.Roles.OFFICE_MANAGER, "مدیر اداری"),
            "supply": (User.Roles.SUPPLY, "واحد تأمین"),
            "reporter": (User.Roles.REPORT_VIEWER, "مدیر گزارش‌گیر"),
        }
        for username, (role, name) in role_users.items():
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"role": role, "full_name_fa": name, "is_staff": False,
                          "email": f"{username}@winac.local"},
            )
            if created:
                user.set_password("test12345")
                user.save()
                self.stdout.write(f"  کاربر {username} ساخته شد (رمز: test12345)")
            elif not user.email:
                # تکمیل ایمیل برای کاربرهای قدیمیِ بدون ایمیل
                user.email = f"{username}@winac.local"
                user.save(update_fields=["email"])

        # پرسنل نمونه
        if not Personnel.objects.exists():
            Personnel.objects.bulk_create([
                Personnel(first_name="علی", last_name="رضایی", personnel_code="1001",
                          org_unit="مالی", person_type=Personnel.PersonType.EMPLOYEE),
                Personnel(first_name="زهرا", last_name="کریمی", personnel_code="1002",
                          org_unit="فناوری اطلاعات", person_type=Personnel.PersonType.EMPLOYEE),
                Personnel(first_name="حسن", last_name="محمدی", personnel_code="1003",
                          org_unit="خدمات", person_type=Personnel.PersonType.SERVICE),
            ])
            self.stdout.write("  ۳ پرسنل نمونه ساخته شد")

        # مهمان نمونه
        if not Guest.objects.exists():
            Guest.objects.create(
                first_name="رضا", last_name="احمدی", company="شرکت نمونه",
                guest_type=Guest.GuestType.CUSTOMER, visit_date=timezone.localdate(),
                needs_lunch=True, approval_status=Guest.ApprovalStatus.APPROVED,
            )
            self.stdout.write("  ۱ مهمان نمونه ساخته شد")

        # کارت‌های مهمان نمونه
        if not GuestCard.objects.exists():
            GuestCard.objects.bulk_create([
                GuestCard(title=f"مهمان {i}", card_code=f"G-{i:03d}") for i in range(1, 6)
            ])
            self.stdout.write("  ۵ کارت مهمان ساخته شد")

        # اقلام پذیرایی نمونه
        if not CateringItem.objects.exists():
            for name, unit in [("میوه", CateringItem.Unit.KILO), ("شیرینی", CateringItem.Unit.KILO),
                               ("چای", CateringItem.Unit.PIECE), ("قهوه", CateringItem.Unit.PIECE),
                               ("آب معدنی", CateringItem.Unit.PIECE), ("کیک", CateringItem.Unit.PIECE)]:
                CateringItem.objects.create(name=name, unit=unit)
            self.stdout.write("  اقلام پذیرایی نمونه ساخته شد")

        # محل‌های پذیرایی نمونه
        if not CateringLocation.objects.exists():
            for name, cap in [("سالن جلسات اصلی", 20), ("اتاق مهمان VIP", 6),
                              ("سالن کنفرانس", 50), ("اتاق مصاحبه", 4)]:
                CateringLocation.objects.create(name=name, capacity=cap)
            self.stdout.write("  محل‌های پذیرایی نمونه ساخته شد")

        self.stdout.write(self.style.SUCCESS("داده‌های نمونه آماده است."))
