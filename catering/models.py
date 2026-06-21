"""مدل‌های مدیریت پذیرایی ویژه مهمان و جلسات (مستقل از فرآیند نهار)."""

from django.db import models

from core.models import TimeStampedModel


class CateringItem(TimeStampedModel):
    """قلم پذیرایی قابل تعریف توسط مدیر (میوه، شیرینی، چای و ...)."""

    class Unit(models.TextChoices):
        PIECE = "piece", "عدد"
        KILO = "kilo", "کیلو"
        PACK = "pack", "بسته"
        PERSON = "person", "نفر"

    name = models.CharField("نام قلم", max_length=100, unique=True)
    unit = models.CharField("واحد شمارش", max_length=10, choices=Unit.choices, default=Unit.PIECE)
    is_active = models.BooleanField("فعال", default=True)
    description = models.TextField("توضیحات", blank=True)

    class Meta:
        verbose_name = "قلم پذیرایی"
        verbose_name_plural = "اقلام پذیرایی"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.get_unit_display()})"


class CateringRequest(TimeStampedModel):
    """درخواست پذیرایی ویژه برای جلسه/مهمان."""

    class Occasion(models.TextChoices):
        MEETING = "meeting", "جلسه"
        VISIT = "visit", "بازدید"
        VIP = "vip", "مهمان ویژه"
        INTERVIEW = "interview", "مصاحبه"
        CEREMONY = "ceremony", "مراسم"
        OTHER = "other", "سایر"

    class Status(models.TextChoices):
        REGISTERED = "registered", "ثبت‌شده"
        PREPARING = "preparing", "در حال آماده‌سازی"
        READY = "ready", "آماده"
        DELIVERED = "delivered", "تحویل‌شده"
        CANCELED = "canceled", "لغو شده"

    title = models.CharField("عنوان درخواست", max_length=150)
    host = models.ForeignKey(
        "people.Personnel",
        verbose_name="درخواست‌دهنده / میزبان",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="catering_requests",
    )
    catering_date = models.DateField("تاریخ پذیرایی", db_index=True)
    prepare_time = models.TimeField("ساعت آماده‌سازی", null=True, blank=True)
    location = models.CharField("محل پذیرایی", max_length=150, blank=True)
    occasion = models.CharField(
        "نوع مناسبت", max_length=15, choices=Occasion.choices, default=Occasion.MEETING
    )
    headcount = models.PositiveIntegerField("تعداد نفرات", default=1)
    status = models.CharField(
        "وضعیت", max_length=15, choices=Status.choices, default=Status.REGISTERED
    )
    description = models.TextField("توضیحات", blank=True)

    class Meta:
        verbose_name = "درخواست پذیرایی"
        verbose_name_plural = "درخواست‌های پذیرایی"
        ordering = ["-catering_date", "-created_at"]

    def __str__(self):
        return f"{self.title} - {self.catering_date}"


class CateringRequestItem(TimeStampedModel):
    """قلم انتخاب‌شده برای یک درخواست پذیرایی به همراه مقدار."""

    request = models.ForeignKey(
        CateringRequest,
        verbose_name="درخواست پذیرایی",
        on_delete=models.CASCADE,
        related_name="items",
    )
    item = models.ForeignKey(
        CateringItem, verbose_name="قلم پذیرایی", on_delete=models.PROTECT, related_name="usages"
    )
    quantity = models.DecimalField("مقدار", max_digits=8, decimal_places=2, default=1)
    description = models.CharField("توضیحات", max_length=255, blank=True)

    class Meta:
        verbose_name = "قلم درخواست پذیرایی"
        verbose_name_plural = "اقلام درخواست پذیرایی"
        ordering = ["item__name"]

    def __str__(self):
        return f"{self.item.name} × {self.quantity}"
