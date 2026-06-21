"""توابع کمکی مشترک، شامل تبدیل تاریخ میلادی به شمسی (بدون وابستگی خارجی)."""

import datetime


# --------------------------------------------------------------------------- #
# تبدیل تاریخ میلادی <-> شمسی (الگوریتم بدون کتابخانه خارجی)
# --------------------------------------------------------------------------- #
def gregorian_to_jalali(gy, gm, gd):
    """یک تاریخ میلادی (سال، ماه، روز) را به (سال، ماه، روز) شمسی تبدیل می‌کند."""
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    gy2 = gy - 1600
    gm2 = gm - 1
    gd2 = gd - 1
    g_day_no = 365 * gy2 + (gy2 + 3) // 4 - (gy2 + 99) // 100 + (gy2 + 399) // 400
    g_day_no += g_d_m[gm2] + gd2
    if gm2 > 1 and ((gy % 4 == 0 and gy % 100 != 0) or (gy % 400 == 0)):
        g_day_no += 1
    j_day_no = g_day_no - 79
    j_np = j_day_no // 12053
    j_day_no %= 12053
    jy = 979 + 33 * j_np + 4 * (j_day_no // 1461)
    j_day_no %= 1461
    if j_day_no >= 366:
        jy += (j_day_no - 366) // 365 + 1
        j_day_no = (j_day_no - 366) % 365
    if j_day_no < 186:
        jm = 1 + j_day_no // 31
        jd = 1 + j_day_no % 31
    else:
        jm = 7 + (j_day_no - 186) // 30
        jd = 1 + (j_day_no - 186) % 30
    return jy, jm, jd


_JALALI_MONTHS = [
    "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند",
]


def to_jalali_str(value, with_month_name=False):
    """یک date یا datetime را به رشتهٔ تاریخ شمسی تبدیل می‌کند. برای None رشتهٔ خالی."""
    if value is None:
        return ""
    if isinstance(value, datetime.datetime):
        value = value.date()
    jy, jm, jd = gregorian_to_jalali(value.year, value.month, value.day)
    if with_month_name:
        return f"{jd} {_JALALI_MONTHS[jm - 1]} {jy}"
    return f"{jy}/{jm:02d}/{jd:02d}"


def jalali_today_str(with_month_name=True):
    from django.utils import timezone

    return to_jalali_str(timezone.localdate(), with_month_name=with_month_name)
