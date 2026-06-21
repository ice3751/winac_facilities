"""مدل‌های مدیریت ژتون غذا، برنامه نهار روزانه و لاگ تلاش تکراری."""

from django.db import models

from core.models import TimeStampedModel


class MealToken(TimeStampedModel):
    """ژتون غذای روزانه و یک‌بارمصرف.

    قاعدهٔ کلیدی: هر گیرنده (پرسنل یا مهمان) در هر روز فقط یک ژتون معتبر دارد.
    این قاعده با UniqueConstraint مشروط (به‌جز ژتون لغوشده) تضمین می‌شود.
    """

    class RecipientType(models.TextChoices):
        PERSONNEL = "personnel", "پرسنل"
        GUEST = "guest", "مهمان"

    class Status(models.TextChoices):
        ISSUED = "issued", "صادر شده"
        CONSUMED = "consumed", "مصرف شده"
        CANCELED = "canceled", "لغو شده"

    date = models.DateField("تاریخ", db_index=True)
    recipient_type = models.CharField(
        "نوع گیرنده", max_length=10, choices=RecipientType.choices
    )
    personnel = models.ForeignKey(
        "people.Personnel",
        verbose_name="پرسنل",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="meal_tokens",
    )
    guest = models.ForeignKey(
        "guests.Guest",
        verbose_name="مهمان",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="meal_tokens",
    )
    token_code = models.CharField("کد ژتون", max_length=30, unique=True)
    status = models.CharField(
        "وضعیت", max_length=10, choices=Status.choices, default=Status.ISSUED
    )
    issued_at = models.DateTimeField("زمان صدور", null=True, blank=True)
    consumed_at = models.DateTimeField("زمان مصرف", null=True, blank=True)
    issued_by = models.ForeignKey(
        "accounts.User",
        verbose_name="صادرکننده",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="issued_tokens",
    )
    consumed_by = models.ForeignKey(
        "accounts.User",
        verbose_name="مسئول ثبت مصرف",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="consumed_tokens",
    )
    description = models.TextField("توضیحات", blank=True)

    class Meta:
        verbose_name = "ژتون غذا"
        verbose_name_plural = "ژتون‌های غذا"
        ordering = ["-date", "-issued_at"]
        constraints = [
            # هر پرسنل در هر روز فقط یک ژتون غیرلغو
            models.UniqueConstraint(
                fields=["date", "personnel"],
                condition=~models.Q(status="canceled") & models.Q(personnel__isnull=False),
                name="unique_personnel_token_per_day",
            ),
            # هر مهمان در هر روز فقط یک ژتون غیرلغو
            models.UniqueConstraint(
                fields=["date", "guest"],
                condition=~models.Q(status="canceled") & models.Q(guest__isnull=False),
                name="unique_guest_token_per_day",
            ),
        ]

    def __str__(self):
        return f"ژتون {self.token_code} - {self.recipient_name}"

    @property
    def recipient_name(self):
        if self.recipient_type == self.RecipientType.PERSONNEL and self.personnel:
            return self.personnel.full_name
        if self.recipient_type == self.RecipientType.GUEST and self.guest:
            return self.guest.full_name
        return "-"


class DailyMealPlan(TimeStampedModel):
    """برنامه/ظرفیت نهار روزانه برای پیش‌بینی تعداد غذا."""

    date = models.DateField("تاریخ", unique=True)
    expected_personnel = models.PositiveIntegerField("غذای پیش‌بینی کارکنان", default=0)
    expected_guests = models.PositiveIntegerField("غذای پیش‌بینی مهمان‌ها", default=0)
    total_ordered = models.PositiveIntegerField("تعداد کل سفارش", default=0)
    description = models.TextField("توضیحات", blank=True)

    class Meta:
        verbose_name = "برنامه نهار روزانه"
        verbose_name_plural = "برنامه‌های نهار روزانه"
        ordering = ["-date"]

    def __str__(self):
        return f"برنامه نهار {self.date}"


class DuplicateAttempt(TimeStampedModel):
    """لاگ تلاش‌های تکراری یا مغایر برای دریافت/مصرف ژتون (برای گزارش مغایرت)."""

    class Kind(models.TextChoices):
        ISSUE = "issue", "تلاش صدور تکراری"
        CONSUME = "consume", "تلاش مصرف نامعتبر"

    date = models.DateField("تاریخ", db_index=True)
    kind = models.CharField("نوع تلاش", max_length=10, choices=Kind.choices)
    recipient_label = models.CharField("گیرنده", max_length=150, blank=True)
    token = models.ForeignKey(
        MealToken,
        verbose_name="ژتون مرتبط",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="duplicate_attempts",
    )
    message = models.CharField("پیام", max_length=255)

    class Meta:
        verbose_name = "تلاش تکراری / مغایرت"
        verbose_name_plural = "تلاش‌های تکراری / مغایرت‌ها"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_kind_display()} - {self.recipient_label}"
