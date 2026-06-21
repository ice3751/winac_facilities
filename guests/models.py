"""مدل‌های مدیریت مهمان، کارت‌های موقت مهمان و تخصیص کارت."""

from django.db import models

from core.models import TimeStampedModel


class Guest(TimeStampedModel):
    """مهمان مراجعه‌کننده به سازمان."""

    class GuestType(models.TextChoices):
        CUSTOMER = "customer", "مشتری"
        CONTRACTOR = "contractor", "پیمانکار"
        SUPPLIER = "supplier", "تأمین‌کننده"
        VISITOR = "visitor", "بازدیدکننده"
        VIP = "vip", "مهمان ویژه"
        OTHER = "other", "سایر"

    class Status(models.TextChoices):
        REGISTERED = "registered", "ثبت‌شده"
        ENTERED = "entered", "وارد شده"
        EXITED = "exited", "خارج شده"
        CANCELED = "canceled", "لغو شده"

    first_name = models.CharField("نام", max_length=80)
    last_name = models.CharField("نام خانوادگی", max_length=80)
    company = models.CharField("شرکت / سازمان", max_length=150, blank=True)
    guest_type = models.CharField(
        "نوع مهمان", max_length=20, choices=GuestType.choices, default=GuestType.VISITOR
    )
    phone = models.CharField("شماره تماس", max_length=20, blank=True)
    host_personnel = models.ForeignKey(
        "people.Personnel",
        verbose_name="میزبان داخلی",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hosted_guests",
    )
    visit_date = models.DateField("تاریخ مراجعه")
    expected_entry_time = models.TimeField("ساعت ورود تقریبی", null=True, blank=True)
    expected_exit_time = models.TimeField("ساعت خروج تقریبی", null=True, blank=True)
    needs_lunch = models.BooleanField("نیاز به نهار", default=False)
    needs_catering = models.BooleanField("نیاز به پذیرایی ویژه", default=False)
    status = models.CharField(
        "وضعیت", max_length=15, choices=Status.choices, default=Status.REGISTERED
    )
    description = models.TextField("توضیحات", blank=True)

    class Meta:
        verbose_name = "مهمان"
        verbose_name_plural = "مهمان‌ها"
        ordering = ["-visit_date", "last_name"]

    def __str__(self):
        return f"{self.full_name} - {self.get_guest_type_display()}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()


class GuestCard(TimeStampedModel):
    """کارت موقت مهمان که هر روز/مراجعه قابل تخصیص مجدد است."""

    class Status(models.TextChoices):
        FREE = "free", "آزاد"
        ASSIGNED = "assigned", "تخصیص داده شده"
        INACTIVE = "inactive", "غیرفعال"

    title = models.CharField("عنوان کارت", max_length=50)  # مثال: مهمان ۱
    card_code = models.CharField("کد کارت", max_length=50, unique=True)
    status = models.CharField(
        "وضعیت", max_length=10, choices=Status.choices, default=Status.FREE
    )
    description = models.TextField("توضیحات", blank=True)

    class Meta:
        verbose_name = "کارت مهمان"
        verbose_name_plural = "کارت‌های مهمان"
        ordering = ["title"]

    def __str__(self):
        return f"{self.title} ({self.card_code})"


class CardAssignment(TimeStampedModel):
    """تخصیص یک کارت موقت به یک مهمان در یک مراجعه."""

    class Status(models.TextChoices):
        ACTIVE = "active", "فعال"
        RETURNED = "returned", "برگشت داده شده"
        LOST = "lost", "مفقود شده"

    guest = models.ForeignKey(
        Guest, verbose_name="مهمان", on_delete=models.CASCADE, related_name="card_assignments"
    )
    card = models.ForeignKey(
        GuestCard, verbose_name="کارت", on_delete=models.PROTECT, related_name="assignments"
    )
    assigned_date = models.DateField("تاریخ تخصیص")
    delivered_at = models.TimeField("ساعت تحویل کارت", null=True, blank=True)
    returned_at = models.TimeField("ساعت برگشت کارت", null=True, blank=True)
    delivered_by = models.ForeignKey(
        "accounts.User",
        verbose_name="تحویل‌دهنده",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="card_deliveries",
    )
    status = models.CharField(
        "وضعیت", max_length=10, choices=Status.choices, default=Status.ACTIVE
    )
    description = models.TextField("توضیحات", blank=True)

    class Meta:
        verbose_name = "تخصیص کارت"
        verbose_name_plural = "تخصیص کارت‌ها"
        ordering = ["-assigned_date"]
        constraints = [
            # یک کارت در آنِ واحد فقط می‌تواند به یک تخصیص فعال متصل باشد.
            models.UniqueConstraint(
                fields=["card"],
                condition=models.Q(status="active"),
                name="unique_active_assignment_per_card",
            )
        ]

    def __str__(self):
        return f"{self.card} → {self.guest}"
