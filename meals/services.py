"""لایه سرویس قواعد کسب‌وکار ژتون غذا.

تمام تصمیم‌گیری‌ها (صدور، جلوگیری از تکرار، مصرف) اینجا متمرکز است تا هم ویوهای
وب و هم پردازش رویدادهای دستگاه تردد (فاز بعد) از یک منطق واحد استفاده کنند.

نکته مهم: ثبت «تلاش تکراری/مغایرت» نباید داخل تراکنشی باشد که در ادامه با خطا
rollback می‌شود؛ در غیر این صورت لاگ مغایرت از بین می‌رود. به همین دلیل لاگ‌ها خارج
از بلوک atomic ساخته می‌شوند و فقط نوشتن نهاییِ موفق در atomic قرار می‌گیرد.
"""

import secrets

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import DuplicateAttempt, MealToken


class MealTokenError(Exception):
    """خطای قابل‌نمایش به کاربر در فرآیند ژتون."""


def lunch_window_open(now=None):
    """آیا اکنون در بازهٔ مجاز صدور ژتون نهار هستیم؟ (تا ساعت تعیین‌شده، پیش‌فرض ۱۰ صبح)."""
    if not getattr(settings, "MEAL_TOKEN_CUTOFF_ENABLED", True):
        return True
    now = now or timezone.localtime()
    return now.hour < getattr(settings, "MEAL_TOKEN_CUTOFF_HOUR", 10)


def lunch_cutoff_message():
    hour = getattr(settings, "MEAL_TOKEN_CUTOFF_HOUR", 10)
    return f"صدور ژتون نهار فقط تا ساعت {hour}:۰۰ صبح همان روز امکان‌پذیر است."


def lunch_assignable_for_date(visit_date, now=None):
    """آیا هنوز می‌توان برای مهمانی که در ``visit_date`` مراجعه می‌کند نهار ثبت کرد؟

    مهلت، ساعت سقف (پیش‌فرض ۱۰ صبح) در «روز مراجعهٔ مهمان» است.
    """
    if not getattr(settings, "MEAL_TOKEN_CUTOFF_ENABLED", True):
        return True
    if visit_date is None:
        return True
    import datetime as _dt

    now = now or timezone.localtime()
    hour = getattr(settings, "MEAL_TOKEN_CUTOFF_HOUR", 10)
    deadline = _dt.datetime.combine(visit_date, _dt.time(hour, 0))
    if timezone.is_naive(deadline):
        deadline = timezone.make_aware(deadline, timezone.get_current_timezone())
    return now < deadline


def generate_token_code():
    """یک کد ژتون یکتای کوتاه و خوانا تولید می‌کند (برای چاپ/QR آینده)."""
    today = timezone.localdate()
    for _ in range(10):
        code = f"{today:%y%m%d}-{secrets.randbelow(10000):04d}"
        if not MealToken.objects.filter(token_code=code).exists():
            return code
    # سقوط بسیار نامحتمل: کد کاملاً تصادفی
    return f"{today:%y%m%d}-{secrets.token_hex(3)}"


def _active_token_for(date, *, personnel=None, guest=None):
    qs = MealToken.objects.exclude(status=MealToken.Status.CANCELED).filter(date=date)
    if personnel is not None:
        return qs.filter(personnel=personnel).first()
    if guest is not None:
        return qs.filter(guest=guest).first()
    return None


def _log_issue_duplicate(date, existing, label, user):
    DuplicateAttempt.objects.create(
        date=date,
        kind=DuplicateAttempt.Kind.ISSUE,
        recipient_label=label,
        token=existing,
        message=f"ژتون تکراری: برای «{label}» در این روز ژتون موجود است.",
        created_by=user,
    )


def issue_token(*, recipient_type, personnel=None, guest=None, user=None, date=None,
                description=""):
    """یک ژتون جدید صادر می‌کند و از تکرار روزانه جلوگیری می‌کند.

    در صورت وجود ژتون معتبر برای همان فرد در همان روز، یک DuplicateAttempt ثبت و
    استثنا MealTokenError پرتاب می‌شود.
    """
    date = date or timezone.localdate()

    if recipient_type == MealToken.RecipientType.PERSONNEL and personnel is None:
        raise MealTokenError("برای صدور ژتون پرسنل، انتخاب پرسنل الزامی است.")
    if recipient_type == MealToken.RecipientType.GUEST and guest is None:
        raise MealTokenError("برای صدور ژتون مهمان، انتخاب مهمان الزامی است.")

    existing = _active_token_for(date, personnel=personnel, guest=guest)
    if existing:
        label = existing.recipient_name
        _log_issue_duplicate(date, existing, label, user)
        raise MealTokenError(
            f"برای «{label}» امروز ژتون «{existing.token_code}» صادر شده است. "
            "هر فرد در هر روز فقط یک ژتون می‌تواند داشته باشد."
        )

    try:
        with transaction.atomic():
            token = MealToken.objects.create(
                date=date,
                recipient_type=recipient_type,
                personnel=personnel,
                guest=guest,
                token_code=generate_token_code(),
                status=MealToken.Status.ISSUED,
                issued_at=timezone.now(),
                issued_by=user,
                created_by=user,
                description=description,
            )
    except IntegrityError:
        # رقابت هم‌زمان: قید دیتابیس مانع تکرار شده است.
        existing = _active_token_for(date, personnel=personnel, guest=guest)
        label = existing.recipient_name if existing else "-"
        _log_issue_duplicate(date, existing, label, user)
        raise MealTokenError("ژتون تکراری است؛ این فرد امروز ژتون دارد.")
    return token


def consume_token(token, *, user=None):
    """یک ژتون را مصرف‌شده می‌کند با اعمال تمام قواعد اعتبار."""
    today = timezone.localdate()

    def _log_invalid(message):
        DuplicateAttempt.objects.create(
            date=today,
            kind=DuplicateAttempt.Kind.CONSUME,
            recipient_label=token.recipient_name,
            token=token,
            message=message,
            created_by=user,
        )

    if token.status == MealToken.Status.CONSUMED:
        msg = f"ژتون «{token.token_code}» قبلاً مصرف شده است."
        _log_invalid(msg)
        raise MealTokenError(msg)
    if token.status == MealToken.Status.CANCELED:
        msg = f"ژتون «{token.token_code}» لغو شده و قابل مصرف نیست."
        _log_invalid(msg)
        raise MealTokenError(msg)
    if token.date != today:
        msg = f"ژتون «{token.token_code}» فقط برای تاریخ {token.date} معتبر است."
        _log_invalid(msg)
        raise MealTokenError(msg)

    with transaction.atomic():
        token.status = MealToken.Status.CONSUMED
        token.consumed_at = timezone.now()
        token.consumed_by = user
        token.save(update_fields=["status", "consumed_at", "consumed_by", "updated_at"])
    return token


def mark_printed(token, *, user=None):
    """چاپ ژتون = مصرف آن.

    وقتی ژتون چاپ می‌شود (با کارت/اثرانگشت روی فیش‌پرینتر یا از صفحهٔ چاپ)، همان لحظه
    «مصرف‌شده» در نظر گرفته می‌شود و نیازی به تأیید مسئول رستوران نیست. اگر ژتون از
    قبل مصرف/لغو شده یا برای روز دیگری باشد، بدون خطا فقط نمایش داده می‌شود.
    """
    if token.status == MealToken.Status.ISSUED and token.date == timezone.localdate():
        with transaction.atomic():
            token.status = MealToken.Status.CONSUMED
            token.consumed_at = timezone.now()
            token.consumed_by = user
            token.save(update_fields=["status", "consumed_at", "consumed_by", "updated_at"])
    return token
