"""لایه آماده‌سازی اتصال آینده به دستگاه تردد.

اکنون هیچ اتصال واقعی انجام نمی‌شود. این مدل‌ها فقط ساختار ثبت رویداد را فراهم
می‌کنند تا در فاز بعد دستگاه تردد بتواند رویداد بفرستد و لایه سرویس ژتون آن را
پردازش کند. منبع تصمیم‌گیری همچنان سایت است، نه دستگاه.
"""

from django.db import models

from core.models import TimeStampedModel


class AttendanceDevice(TimeStampedModel):
    """دستگاه تردد ثبت‌شده در سیستم (برای فاز اتصال)."""

    class DeviceType(models.TextChoices):
        ORG_ENTRANCE = "org_entrance", "ورودی سازمان"
        RESTAURANT = "restaurant", "رستوران"
        OTHER = "other", "سایر"

    device_id = models.CharField("شناسه دستگاه", max_length=64, unique=True)
    name = models.CharField("نام دستگاه", max_length=120, blank=True)
    device_type = models.CharField(
        "نوع دستگاه", max_length=20, choices=DeviceType.choices, default=DeviceType.OTHER
    )
    is_active = models.BooleanField("فعال", default=True)
    description = models.TextField("توضیحات", blank=True)

    class Meta:
        verbose_name = "دستگاه تردد"
        verbose_name_plural = "دستگاه‌های تردد"
        ordering = ["device_id"]

    def __str__(self):
        return self.name or self.device_id


class AttendanceEvent(TimeStampedModel):
    """رویداد خام ثبت‌شده توسط دستگاه تردد، آماده پردازش در فاز بعد."""

    class EventType(models.TextChoices):
        ENTRY = "entry", "ورود"
        EXIT = "exit", "خروج"
        MEAL_REQUEST = "meal_request", "درخواست غذا"

    class ProcessingStatus(models.TextChoices):
        PENDING = "pending", "پردازش‌نشده"
        PROCESSED = "processed", "پردازش‌شده"
        ERROR = "error", "خطا"

    device = models.ForeignKey(
        AttendanceDevice,
        verbose_name="دستگاه",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
    )
    device_type = models.CharField(
        "نوع دستگاه", max_length=20, choices=AttendanceDevice.DeviceType.choices, blank=True
    )
    card_or_fingerprint = models.CharField("شناسه کارت / اثر انگشت", max_length=128, db_index=True)
    occurred_at = models.DateTimeField("تاریخ و ساعت ثبت")
    event_type = models.CharField(
        "نوع رویداد", max_length=15, choices=EventType.choices, default=EventType.ENTRY
    )
    processing_status = models.CharField(
        "وضعیت پردازش",
        max_length=10,
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.PENDING,
        db_index=True,
    )
    error_message = models.TextField("پیام خطا", blank=True)
    raw_data = models.JSONField("داده خام", null=True, blank=True)

    class Meta:
        verbose_name = "رویداد تردد"
        verbose_name_plural = "رویدادهای تردد"
        ordering = ["-occurred_at"]

    def __str__(self):
        return f"{self.get_event_type_display()} - {self.card_or_fingerprint} @ {self.occurred_at}"

    @property
    def device_id_label(self):
        if self.device:
            return self.device.device_id
        return self.device_type or "نامشخص"
