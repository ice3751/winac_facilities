"""مدل‌های پایه و مشترک بین اپ‌ها."""

from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):
    """مدل پایه با فیلدهای زمان ایجاد/ویرایش و ثبت‌کننده.

    تمام مدل‌های اصلی سیستم از این کلاس ارث می‌برند تا ردگیری (audit) یکنواخت باشد.
    """

    created_at = models.DateTimeField("زمان ایجاد", auto_now_add=True)
    updated_at = models.DateTimeField("زمان ویرایش", auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="ثبت‌کننده",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )

    class Meta:
        abstract = True
        ordering = ["-created_at"]
