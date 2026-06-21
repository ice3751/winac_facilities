"""مدل مدیریت پرسنل و عوامل سازمان."""

from django.db import models

from core.models import TimeStampedModel


class Personnel(TimeStampedModel):
    """فرد سازمانی: کارمند، نیروی خدماتی، پیمانکار، راننده و غیره."""

    class PersonType(models.TextChoices):
        EMPLOYEE = "employee", "کارمند"
        SERVICE = "service", "نیروی خدماتی"
        CONTRACTOR = "contractor", "پیمانکار ثابت"
        DRIVER = "driver", "راننده"
        OTHER = "other", "سایر"

    first_name = models.CharField("نام", max_length=80)
    last_name = models.CharField("نام خانوادگی", max_length=80)
    personnel_code = models.CharField("کد پرسنلی", max_length=30, unique=True)
    org_unit = models.CharField("واحد سازمانی", max_length=120, blank=True)
    person_type = models.CharField(
        "نوع فرد", max_length=20, choices=PersonType.choices, default=PersonType.EMPLOYEE
    )
    is_active = models.BooleanField("فعال", default=True)
    # شناسه کارت یا تردد برای اتصال آینده به دستگاه (اکنون استفاده نمی‌شود)
    card_id = models.CharField(
        "شناسه کارت / تردد", max_length=64, blank=True, null=True, unique=True
    )
    description = models.TextField("توضیحات", blank=True)

    class Meta:
        verbose_name = "پرسنل"
        verbose_name_plural = "پرسنل"
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.full_name} ({self.personnel_code})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
