"""مدل کاربر سفارشی با نقش سازمانی."""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """کاربر سیستم با فیلد نقش برای کنترل دسترسی و منوسازی."""

    class Roles(models.TextChoices):
        ADMIN = "admin", "مدیر سیستم"
        RECEPTION = "reception", "پذیرش / نگهبانی"
        RESTAURANT = "restaurant", "مسئول رستوران"
        PROTOCOL = "protocol", "واحد تشریفات"
        HOST = "host", "مدیر واحد / میزبان"
        OFFICE_MANAGER = "office_manager", "مدیر اداری"
        REPORT_VIEWER = "report_viewer", "مدیر گزارش‌گیر"

    role = models.CharField(
        "نقش سازمانی",
        max_length=20,
        choices=Roles.choices,
        default=Roles.HOST,
    )
    full_name_fa = models.CharField("نام کامل (فارسی)", max_length=150, blank=True)

    class Meta:
        verbose_name = "کاربر"
        verbose_name_plural = "کاربران"

    def __str__(self):
        return self.full_name_fa or self.get_full_name() or self.username

    @property
    def display_name(self):
        return self.full_name_fa or self.get_full_name() or self.username

    # دسترسی‌های میان‌بر برای استفاده در قالب‌ها و ویوها
    @property
    def is_admin_role(self):
        return self.is_superuser or self.role == self.Roles.ADMIN

    def has_role(self, *roles):
        return self.is_admin_role or self.role in roles
