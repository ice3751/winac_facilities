"""پردازش رویدادهای دستگاه تردد (فاز ۵).

این لایه رویداد خام دستگاه را می‌گیرد و در صورت نیاز، تصمیم‌گیری را به لایهٔ سرویس
ژتون (`meals.services`) می‌سپارد. منبع تصمیم همچنان سایت است؛ دستگاه فقط رویداد
تولید می‌کند. صدور واقعی ژتون و قاعدهٔ «یک ژتون در روز» در همان لایهٔ موجود اعمال
می‌شود و کد تکراری نمی‌شود.
"""

from django.utils import timezone

from meals.models import MealToken
from meals.services import MealTokenError, issue_token
from people.models import Personnel

from .models import AttendanceEvent


def _resolve_personnel(card_or_fingerprint):
    """یافتن پرسنل فعال بر اساس شناسه کارت/تردد."""
    if not card_or_fingerprint:
        return None
    return Personnel.objects.filter(
        card_id=card_or_fingerprint, is_active=True
    ).first()


def process_event(event, *, user=None):
    """یک رویداد تردد را پردازش می‌کند و وضعیت پردازش آن را به‌روزرسانی می‌کند.

    - رویداد «درخواست غذا»: در صورت یافتن پرسنل، ژتون روز صادر می‌شود (با همان قواعد
      ضدتکرار). تکراری بودن یا کارت ناشناخته به‌صورت وضعیت «خطا» با پیام ثبت می‌شود.
    - رویداد ورود/خروج: فعلاً فقط «پردازش‌شده» علامت می‌خورد (قلاب برای فاز بعد).
    """
    if event.processing_status == AttendanceEvent.ProcessingStatus.PROCESSED:
        return event

    def _mark(status, error=""):
        event.processing_status = status
        event.error_message = error
        event.save(update_fields=["processing_status", "error_message", "updated_at"])
        return event

    if event.event_type == AttendanceEvent.EventType.MEAL_REQUEST:
        personnel = _resolve_personnel(event.card_or_fingerprint)
        if personnel is None:
            return _mark(
                AttendanceEvent.ProcessingStatus.ERROR,
                f"کارت ناشناخته یا غیرفعال: {event.card_or_fingerprint}",
            )
        try:
            issue_token(
                recipient_type=MealToken.RecipientType.PERSONNEL,
                personnel=personnel,
                user=user,
                date=timezone.localdate(event.occurred_at) if event.occurred_at else None,
                description=f"صدور خودکار از دستگاه {event.device_id_label}",
            )
        except MealTokenError as exc:
            # تکراری بودن یک نتیجهٔ معنادار است؛ به‌صورت خطای پردازش ثبت می‌شود
            return _mark(AttendanceEvent.ProcessingStatus.ERROR, str(exc))
        return _mark(AttendanceEvent.ProcessingStatus.PROCESSED)

    # ورود/خروج: قلاب آماده برای فاز بعد (مثلاً به‌روزرسانی وضعیت مهمان)
    return _mark(AttendanceEvent.ProcessingStatus.PROCESSED)


def process_pending(limit=None, *, user=None):
    """پردازش دسته‌ای رویدادهای پردازش‌نشده. تعداد پردازش‌شده را برمی‌گرداند."""
    qs = AttendanceEvent.objects.filter(
        processing_status=AttendanceEvent.ProcessingStatus.PENDING
    ).order_by("occurred_at")
    if limit:
        qs = qs[:limit]
    count = 0
    for event in list(qs):
        process_event(event, user=user)
        count += 1
    return count
