"""تعریف گزارش‌ها به‌صورت توابع مستقل.

هر گزارش یک تابع است که بازهٔ تاریخ را می‌گیرد و یک دیکشنری شامل عنوان، سرستون‌ها و
ردیف‌ها برمی‌گرداند. همین خروجی هم برای نمایش HTML و هم برای خروجی Excel استفاده
می‌شود تا منطق گزارش یک‌جا متمرکز بماند.
"""

from django.db.models import Count, Q

from catering.models import CateringItem, CateringRequest, CateringRequestItem
from guests.models import Guest
from meals.models import DuplicateAttempt, MealToken
from people.models import Personnel


def _result(title, headers, rows):
    return {"title": title, "headers": headers, "rows": rows}


def _tokens_in_range(start, end):
    return MealToken.objects.filter(date__range=(start, end))


def daily_consumption(start, end):
    """مصرف غذای روزانه (به تفکیک روز)."""
    qs = (
        _tokens_in_range(start, end)
        .values("date")
        .annotate(
            issued=Count("id", filter=~Q(status=MealToken.Status.CANCELED)),
            consumed=Count("id", filter=Q(status=MealToken.Status.CONSUMED)),
        )
        .order_by("date")
    )
    rows = [[r["date"], r["issued"], r["consumed"], r["issued"] - r["consumed"]] for r in qs]
    return _result("گزارش مصرف غذای روزانه",
                   ["تاریخ", "صادرشده", "مصرف‌شده", "مصرف‌نشده"], rows)


def consumption_range(start, end):
    """فهرست تفصیلی ژتون‌های مصرف‌شده در بازه."""
    qs = (
        _tokens_in_range(start, end)
        .filter(status=MealToken.Status.CONSUMED)
        .select_related("personnel", "guest")
        .order_by("date")
    )
    rows = [[t.date, t.token_code, t.get_recipient_type_display(), t.recipient_name,
             t.consumed_at.strftime("%H:%M") if t.consumed_at else "-"] for t in qs]
    return _result("گزارش مصرف غذا در بازه تاریخی",
                   ["تاریخ", "کد ژتون", "نوع گیرنده", "گیرنده", "ساعت مصرف"], rows)


def by_org_unit(start, end):
    """غذای مصرف‌شده پرسنل به تفکیک واحد سازمانی."""
    qs = (
        _tokens_in_range(start, end)
        .filter(status=MealToken.Status.CONSUMED, personnel__isnull=False)
        .values("personnel__org_unit")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
    rows = [[r["personnel__org_unit"] or "نامشخص", r["total"]] for r in qs]
    return _result("گزارش غذا به تفکیک واحد سازمانی", ["واحد سازمانی", "تعداد"], rows)


def by_person_type(start, end):
    """غذای مصرف‌شده پرسنل به تفکیک نوع فرد."""
    qs = (
        _tokens_in_range(start, end)
        .filter(status=MealToken.Status.CONSUMED, personnel__isnull=False)
        .values("personnel__person_type")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
    label = dict(Personnel.PersonType.choices)
    rows = [[label.get(r["personnel__person_type"], "نامشخص"), r["total"]] for r in qs]
    return _result("گزارش غذا به تفکیک نوع فرد", ["نوع فرد", "تعداد"], rows)


def guest_meals(start, end):
    """گزارش ژتون‌های غذای مهمان‌ها."""
    qs = (
        _tokens_in_range(start, end)
        .filter(guest__isnull=False)
        .exclude(status=MealToken.Status.CANCELED)
        .select_related("guest")
        .order_by("date")
    )
    rows = [[t.date, t.recipient_name, t.guest.company, t.get_status_display()] for t in qs]
    return _result("گزارش غذای مهمان‌ها", ["تاریخ", "مهمان", "شرکت", "وضعیت"], rows)


def guests_by_host(start, end):
    """تعداد مهمان به تفکیک میزبان داخلی."""
    qs = (
        Guest.objects.filter(visit_date__range=(start, end))
        .values("host_personnel__first_name", "host_personnel__last_name")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
    rows = []
    for r in qs:
        name = f"{r['host_personnel__first_name'] or ''} {r['host_personnel__last_name'] or ''}".strip()
        rows.append([name or "بدون میزبان", r["total"]])
    return _result("گزارش مهمان‌ها به تفکیک میزبان", ["میزبان", "تعداد مهمان"], rows)


def issued_vs_consumed(start, end):
    """خلاصه ژتون‌های صادرشده و مصرف‌شده به تفکیک روز."""
    return _result("گزارش ژتون‌های صادرشده و مصرف‌شده",
                   ["تاریخ", "صادرشده", "مصرف‌شده", "مصرف‌نشده"],
                   daily_consumption(start, end)["rows"])


def issued_not_consumed(start, end):
    """ژتون‌های صادرشده ولی مصرف‌نشده."""
    qs = (
        _tokens_in_range(start, end)
        .filter(status=MealToken.Status.ISSUED)
        .select_related("personnel", "guest")
        .order_by("date")
    )
    rows = [[t.date, t.token_code, t.get_recipient_type_display(), t.recipient_name] for t in qs]
    return _result("گزارش ژتون‌های صادرشده ولی مصرف‌نشده",
                   ["تاریخ", "کد ژتون", "نوع گیرنده", "گیرنده"], rows)


def duplicate_attempts(start, end):
    """تلاش‌های تکراری/مغایر."""
    qs = DuplicateAttempt.objects.filter(date__range=(start, end)).order_by("-created_at")
    rows = [[d.date, d.get_kind_display(), d.recipient_label, d.message] for d in qs]
    return _result("گزارش تلاش تکراری برای دریافت غذا",
                   ["تاریخ", "نوع", "گیرنده", "پیام"], rows)


def special_catering(start, end):
    """درخواست‌های پذیرایی ویژه در بازه."""
    qs = (
        CateringRequest.objects.filter(catering_date__range=(start, end))
        .select_related("host")
        .order_by("catering_date")
    )
    rows = [[c.catering_date, c.title, c.host.full_name if c.host else "-",
             c.get_occasion_display(), c.headcount, c.get_status_display()] for c in qs]
    return _result("گزارش پذیرایی‌های ویژه",
                   ["تاریخ", "عنوان", "میزبان", "مناسبت", "نفرات", "وضعیت"], rows)


def catering_items(start, end):
    """اقلام مصرف‌شده پذیرایی در بازه."""
    qs = (
        CateringRequestItem.objects.filter(request__catering_date__range=(start, end))
        .values("item__name", "item__unit")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
    unit_label = dict(CateringItem.Unit.choices)
    rows = [[r["item__name"], unit_label.get(r["item__unit"], ""), r["total"]] for r in qs]
    return _result("گزارش اقلام مصرف‌شده پذیرایی",
                   ["قلم", "واحد", "تعداد دفعات استفاده"], rows)


# رجیستری گزارش‌ها: کلید → (تابع)
REPORTS = {
    "daily_consumption": daily_consumption,
    "consumption_range": consumption_range,
    "by_org_unit": by_org_unit,
    "by_person_type": by_person_type,
    "guest_meals": guest_meals,
    "guests_by_host": guests_by_host,
    "issued_vs_consumed": issued_vs_consumed,
    "issued_not_consumed": issued_not_consumed,
    "duplicate_attempts": duplicate_attempts,
    "special_catering": special_catering,
    "catering_items": catering_items,
}

REPORT_TITLES = {
    "daily_consumption": "مصرف غذای روزانه",
    "consumption_range": "مصرف غذا در بازه تاریخی",
    "by_org_unit": "غذا به تفکیک واحد سازمانی",
    "by_person_type": "غذا به تفکیک نوع فرد",
    "guest_meals": "غذای مهمان‌ها",
    "guests_by_host": "مهمان‌ها به تفکیک میزبان",
    "issued_vs_consumed": "ژتون‌های صادرشده و مصرف‌شده",
    "issued_not_consumed": "ژتون‌های صادرشده ولی مصرف‌نشده",
    "duplicate_attempts": "تلاش تکراری دریافت غذا",
    "special_catering": "پذیرایی‌های ویژه",
    "catering_items": "اقلام مصرف‌شده پذیرایی",
}
