"""API داخلی دریافت رویداد از دستگاه تردد (فاز ۵).

دستگاه یک درخواست POST با بدنهٔ JSON و هدر احراز هویت ``X-API-KEY`` می‌فرستد.
رویداد ذخیره و (به‌صورت پیش‌فرض) بلافاصله پردازش می‌شود. اگر کلید API تنظیم نشده
باشد، endpoint غیرفعال است تا به‌اشتباه در دسترس قرار نگیرد.
"""

import json

from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_exempt

from .models import AttendanceDevice, AttendanceEvent
from .services import process_event


@csrf_exempt
def ingest_event(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "فقط POST مجاز است"}, status=405)

    # احراز هویت دستگاه با کلید مشترک
    api_key = settings.DEVICE_API_KEY
    if not api_key:
        return JsonResponse(
            {"ok": False, "error": "API دستگاه غیرفعال است (DEVICE_API_KEY تنظیم نشده)"},
            status=503,
        )
    if request.headers.get("X-API-KEY") != api_key:
        return JsonResponse({"ok": False, "error": "کلید API نامعتبر"}, status=401)

    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "بدنهٔ JSON نامعتبر"}, status=400)

    card = (payload.get("card_or_fingerprint") or "").strip()
    if not card:
        return JsonResponse(
            {"ok": False, "error": "فیلد card_or_fingerprint الزامی است"}, status=400
        )

    event_type = payload.get("event_type", AttendanceEvent.EventType.MEAL_REQUEST)
    valid_types = dict(AttendanceEvent.EventType.choices)
    if event_type not in valid_types:
        return JsonResponse(
            {"ok": False, "error": f"event_type نامعتبر: {event_type}"}, status=400
        )

    # تطبیق دستگاه (در صورت ارسال device_id)
    device = None
    device_id = payload.get("device_id")
    if device_id:
        device = AttendanceDevice.objects.filter(device_id=device_id).first()

    occurred_at = parse_datetime(payload.get("occurred_at", "")) or timezone.now()

    event = AttendanceEvent.objects.create(
        device=device,
        device_type=(device.device_type if device else payload.get("device_type", "")),
        card_or_fingerprint=card,
        occurred_at=occurred_at,
        event_type=event_type,
        raw_data=payload,
    )

    # پردازش فوری (مگر اینکه درخواست تأخیر شده باشد)
    if payload.get("defer") is not True:
        process_event(event)

    return JsonResponse({
        "ok": True,
        "event_id": event.id,
        "processing_status": event.processing_status,
        "message": event.error_message or "ثبت و پردازش شد",
    }, status=201)
