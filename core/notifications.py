"""اطلاع‌رسانی ایمیلی به مدیر اداری و میزبان‌ها.

طبق نیاز: فقط برای میزبان‌ها (نقش host) و مدیر اداری ایمیل ارسال می‌شود.
- هنگام ثبت درخواست جدید (مهمان یا پذیرایی) که در انتظار تأیید است → به مدیر اداری.
- پس از تصمیم مدیر اداری (تأیید/رد) → به میزبانِ ثبت‌کنندهٔ درخواست.

ارسال ایمیل هرگز نباید جریان اصلی برنامه را مختل کند؛ بنابراین خطاها بی‌صدا لاگ
می‌شوند و استثنا پرتاب نمی‌شود.
"""

import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def _office_manager_emails():
    from accounts.models import User

    return list(
        User.objects.filter(role=User.Roles.OFFICE_MANAGER, is_active=True)
        .exclude(email="")
        .values_list("email", flat=True)
    )


def _user_email(user):
    return [user.email] if (user and user.email) else []


def _send(subject, body, recipients):
    if not getattr(settings, "NOTIFY_EMAIL_ENABLED", True):
        return
    recipients = [r for r in (recipients or []) if r]
    if not recipients:
        return
    try:
        send_mail(
            subject,
            body,
            getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipients,
            fail_silently=False,
        )
    except Exception:  # pragma: no cover - ارسال ایمیل نباید برنامه را بشکند
        logger.exception("ارسال ایمیل اطلاع‌رسانی ناموفق بود: %s", subject)


# --------------------------------------------------------------------------- #
# مهمان
# --------------------------------------------------------------------------- #
def notify_office_new_guest(guest):
    """به مدیر اداری: یک مهمان جدید در انتظار تأیید است."""
    creator = guest.created_by.display_name if guest.created_by else "—"
    _send(
        "[ویناک] مهمان جدید در انتظار تأیید",
        (
            f"یک مهمان جدید برای تأیید در کارتابل شما ثبت شد:\n\n"
            f"نام مهمان: {guest.full_name}\n"
            f"شرکت: {guest.company or '—'}\n"
            f"تاریخ مراجعه: {guest.visit_date}\n"
            f"ثبت‌کننده (میزبان): {creator}\n\n"
            f"برای بررسی به بخش «تأیید مهمان‌ها» مراجعه کنید."
        ),
        _office_manager_emails(),
    )


def notify_host_guest_decision(guest):
    """به میزبانِ ثبت‌کننده: نتیجهٔ تأیید مهمان."""
    decision = "تأیید" if guest.approval_status == guest.ApprovalStatus.APPROVED else "رد"
    body = (
        f"درخواست مهمان شما بررسی شد.\n\n"
        f"نام مهمان: {guest.full_name}\n"
        f"تاریخ مراجعه: {guest.visit_date}\n"
        f"نتیجه: {decision} شد.\n"
    )
    if guest.review_note:
        body += f"توضیح مدیر اداری: {guest.review_note}\n"
    _send(f"[ویناک] درخواست مهمان شما {decision} شد", body, _user_email(guest.created_by))


# --------------------------------------------------------------------------- #
# پذیرایی
# --------------------------------------------------------------------------- #
def notify_office_new_catering(req):
    """به مدیر اداری: یک درخواست پذیرایی جدید در انتظار تأیید است."""
    creator = req.created_by.display_name if req.created_by else "—"
    _send(
        "[ویناک] درخواست پذیرایی جدید در انتظار تأیید",
        (
            f"یک درخواست پذیرایی جدید برای تأیید در کارتابل شما ثبت شد:\n\n"
            f"عنوان: {req.title}\n"
            f"تاریخ پذیرایی: {req.catering_date}\n"
            f"محل: {req.location.name if req.location else '—'}\n"
            f"تعداد نفرات: {req.headcount}\n"
            f"ثبت‌کننده: {creator}\n\n"
            f"برای بررسی به بخش «تأیید پذیرایی» مراجعه کنید."
        ),
        _office_manager_emails(),
    )


def notify_host_catering_decision(req):
    """به ثبت‌کنندهٔ درخواست پذیرایی: نتیجهٔ تأیید."""
    decision = "تأیید" if req.approval_status == req.ApprovalStatus.APPROVED else "رد"
    body = (
        f"درخواست پذیرایی شما بررسی شد.\n\n"
        f"عنوان: {req.title}\n"
        f"تاریخ پذیرایی: {req.catering_date}\n"
        f"نتیجه: {decision} شد.\n"
    )
    if req.review_note:
        body += f"توضیح مدیر اداری: {req.review_note}\n"
    _send(f"[ویناک] درخواست پذیرایی شما {decision} شد", body, _user_email(req.created_by))
