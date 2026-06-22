"""تست‌های دود برای اطمینان از بارگذاری صفحات و قواعد کلیدی ژتون."""

import json

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from attendance.models import AttendanceEvent
from attendance.services import process_event
from guests.models import Guest
from meals.models import DuplicateAttempt, MealToken
from meals.services import MealTokenError, consume_token, issue_token
from people.models import Personnel


class PageSmokeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser(
            username="admin_t", password="pass12345", role=User.Roles.ADMIN
        )
        cls.person = Personnel.objects.create(
            first_name="آزمون", last_name="نمونه", personnel_code="9001"
        )
        cls.guest = Guest.objects.create(
            first_name="مهمان", last_name="آزمون", visit_date=timezone.localdate()
        )

    def setUp(self):
        self.client.force_login(self.admin)

    def test_pages_load(self):
        for name in [
            "dashboard:home", "people:list", "people:add", "guests:list",
            "guests:cards", "guests:assignments", "guests:assignment_add",
            "guests:approvals", "meals:issue", "meals:consume",
            "meals:today", "meals:plans", "catering:list", "catering:items",
            "reports:index",
        ]:
            with self.subTest(url=name):
                resp = self.client.get(reverse(name))
                self.assertEqual(resp.status_code, 200, f"{name} → {resp.status_code}")

    def test_report_excel_export(self):
        url = reverse("reports:detail", args=["daily_consumption"])
        resp = self.client.get(url, {"export": "excel"})
        self.assertEqual(resp.status_code, 200)
        self.assertIn("spreadsheetml", resp["Content-Type"])


class MealTokenRuleTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = Personnel.objects.create(
            first_name="علی", last_name="رضایی", personnel_code="8001"
        )

    def test_issue_then_duplicate_blocked(self):
        token = issue_token(
            recipient_type=MealToken.RecipientType.PERSONNEL, personnel=self.person
        )
        self.assertEqual(token.status, MealToken.Status.ISSUED)
        # تلاش دوم در همان روز باید رد شود و در لاگ مغایرت ثبت گردد
        with self.assertRaises(MealTokenError):
            issue_token(
                recipient_type=MealToken.RecipientType.PERSONNEL, personnel=self.person
            )
        self.assertEqual(DuplicateAttempt.objects.filter(
            kind=DuplicateAttempt.Kind.ISSUE).count(), 1)

    def test_consume_once_then_blocked(self):
        token = issue_token(
            recipient_type=MealToken.RecipientType.PERSONNEL, personnel=self.person
        )
        consume_token(token)
        self.assertEqual(token.status, MealToken.Status.CONSUMED)
        # مصرف دوباره باید رد شود
        with self.assertRaises(MealTokenError):
            consume_token(token)

    def test_reissue_after_cancel_allowed(self):
        token = issue_token(
            recipient_type=MealToken.RecipientType.PERSONNEL, personnel=self.person
        )
        token.status = MealToken.Status.CANCELED
        token.save(update_fields=["status"])
        # پس از لغو، صدور مجدد برای همان روز باید مجاز باشد
        token2 = issue_token(
            recipient_type=MealToken.RecipientType.PERSONNEL, personnel=self.person
        )
        self.assertNotEqual(token.pk, token2.pk)


@override_settings(DEVICE_API_KEY="test-key")
class AttendanceIntegrationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = Personnel.objects.create(
            first_name="کارت", last_name="دار", personnel_code="7001", card_id="CARD-7001"
        )

    def _make_event(self, card="CARD-7001"):
        return AttendanceEvent.objects.create(
            card_or_fingerprint=card,
            occurred_at=timezone.now(),
            event_type=AttendanceEvent.EventType.MEAL_REQUEST,
        )

    def test_meal_request_issues_token(self):
        event = self._make_event()
        process_event(event)
        self.assertEqual(event.processing_status, AttendanceEvent.ProcessingStatus.PROCESSED)
        self.assertEqual(MealToken.objects.filter(personnel=self.person).count(), 1)

    def test_duplicate_request_marks_error(self):
        process_event(self._make_event())
        event2 = self._make_event()
        process_event(event2)
        # دومین درخواست در همان روز باید با وضعیت خطا (تکراری) ثبت شود
        self.assertEqual(event2.processing_status, AttendanceEvent.ProcessingStatus.ERROR)
        self.assertEqual(MealToken.objects.filter(personnel=self.person).count(), 1)

    def test_unknown_card_marks_error(self):
        event = self._make_event(card="UNKNOWN")
        process_event(event)
        self.assertEqual(event.processing_status, AttendanceEvent.ProcessingStatus.ERROR)

    def test_api_requires_valid_key(self):
        url = reverse("attendance:ingest_event")
        body = json.dumps({"card_or_fingerprint": "CARD-7001"})
        # کلید نادرست
        resp = self.client.post(url, body, content_type="application/json",
                                HTTP_X_API_KEY="wrong")
        self.assertEqual(resp.status_code, 401)
        # کلید درست → ساخت و پردازش رویداد
        resp = self.client.post(url, body, content_type="application/json",
                                HTTP_X_API_KEY="test-key")
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(resp.json()["ok"])
        self.assertEqual(MealToken.objects.filter(personnel=self.person).count(), 1)


class GuestApprovalTests(TestCase):
    def setUp(self):
        self.host = User.objects.create_user(
            username="host_t", password="pass12345", role=User.Roles.HOST
        )
        self.office = User.objects.create_user(
            username="office_t", password="pass12345", role=User.Roles.OFFICE_MANAGER
        )

    def test_host_registration_is_pending(self):
        self.client.force_login(self.host)
        resp = self.client.post(reverse("guests:add"), {
            "first_name": "مهمان", "last_name": "تست", "company": "",
            "guest_type": Guest.GuestType.VISITOR, "phone": "",
            "visit_date": timezone.localdate().isoformat(),
            "needs_lunch": "on", "status": Guest.Status.REGISTERED,
        })
        self.assertEqual(resp.status_code, 302)
        guest = Guest.objects.get(first_name="مهمان")
        self.assertEqual(guest.approval_status, Guest.ApprovalStatus.PENDING)

    def test_office_manager_can_approve(self):
        guest = Guest.objects.create(
            first_name="در", last_name="انتظار", visit_date=timezone.localdate(),
            approval_status=Guest.ApprovalStatus.PENDING,
        )
        self.client.force_login(self.office)
        resp = self.client.post(reverse("guests:review", args=[guest.pk]),
                                {"decision": "approve", "review_note": "اوکی"})
        self.assertEqual(resp.status_code, 302)
        guest.refresh_from_db()
        self.assertEqual(guest.approval_status, Guest.ApprovalStatus.APPROVED)
        self.assertEqual(guest.approved_by, self.office)

    def test_host_cannot_access_approvals(self):
        self.client.force_login(self.host)
        resp = self.client.get(reverse("guests:approvals"))
        self.assertEqual(resp.status_code, 403)


class CateringLocationConflictTests(TestCase):
    def setUp(self):
        from catering.models import CateringLocation
        self.protocol = User.objects.create_user(
            username="proto_t", password="pass12345", role=User.Roles.PROTOCOL
        )
        self.loc = CateringLocation.objects.create(name="سالن تست")
        self.client.force_login(self.protocol)

    def _payload(self, start, end, title="جلسه"):
        return {
            "title": title, "catering_date": timezone.localdate().isoformat(),
            "location": self.loc.pk, "start_time": start, "end_time": end,
            "occasion": "meeting", "headcount": 5, "status": "registered",
            # فرم‌ست اقلام (خالی)
            "items-TOTAL_FORMS": "0", "items-INITIAL_FORMS": "0",
            "items-MIN_NUM_FORMS": "0", "items-MAX_NUM_FORMS": "1000",
        }

    def test_overlapping_booking_rejected(self):
        from catering.models import CateringRequest
        r1 = self.client.post(reverse("catering:add"), self._payload("10:00", "11:00"))
        self.assertEqual(r1.status_code, 302)
        self.assertEqual(CateringRequest.objects.count(), 1)
        # بازهٔ متداخل برای همان محل باید رد شود
        r2 = self.client.post(reverse("catering:add"),
                              self._payload("10:30", "11:30", title="جلسه دوم"))
        self.assertEqual(r2.status_code, 200)  # فرم با خطا برمی‌گردد
        self.assertEqual(CateringRequest.objects.count(), 1)

    def test_non_overlapping_booking_allowed(self):
        from catering.models import CateringRequest
        self.client.post(reverse("catering:add"), self._payload("10:00", "11:00"))
        r2 = self.client.post(reverse("catering:add"),
                             self._payload("11:00", "12:00", title="جلسه دوم"))
        self.assertEqual(r2.status_code, 302)
        self.assertEqual(CateringRequest.objects.count(), 2)

    def test_create_with_inline_items_flows_to_supply(self):
        from catering.models import CateringItem, CateringRequestItem
        item = CateringItem.objects.create(name="شیرینی")
        payload = self._payload("13:00", "14:00", title="جلسه با اقلام")
        payload.update({
            "items-TOTAL_FORMS": "1",
            "items-0-item": item.pk,
            "items-0-quantity": "3",
            "items-0-needs_purchase": "on",
            "items-0-description": "",
        })
        resp = self.client.post(reverse("catering:add"), payload)
        self.assertEqual(resp.status_code, 302)
        cri = CateringRequestItem.objects.get(item=item)
        self.assertTrue(cri.needs_purchase)
        self.assertEqual(cri.purchase_status, CateringRequestItem.PurchaseStatus.PENDING)


class SupplyPanelTests(TestCase):
    def setUp(self):
        from catering.models import (CateringItem, CateringRequest,
                                     CateringRequestItem)
        self.supply = User.objects.create_user(
            username="supply_t", password="pass12345", role=User.Roles.SUPPLY
        )
        item = CateringItem.objects.create(name="میوه")
        req = CateringRequest.objects.create(
            title="جلسه", catering_date=timezone.localdate(), headcount=3
        )
        self.cri = CateringRequestItem.objects.create(
            request=req, item=item, quantity=2, needs_purchase=True
        )

    def test_supply_sees_and_marks_purchased(self):
        from catering.models import CateringRequestItem
        self.client.force_login(self.supply)
        resp = self.client.get(reverse("catering:supply"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "میوه")
        # علامت‌گذاری تهیه‌شده
        self.client.post(reverse("catering:supply_purchased", args=[self.cri.pk]))
        self.cri.refresh_from_db()
        self.assertEqual(self.cri.purchase_status,
                         CateringRequestItem.PurchaseStatus.PURCHASED)
        self.assertEqual(self.cri.purchased_by, self.supply)


class ChartHelperTests(TestCase):
    def test_bar_chart_renders_svg(self):
        from core.charts import bar_chart

        svg = bar_chart(["شنبه", "یک‌شنبه"], [{"values": [3, 5], "cls": "bar-a"}])
        self.assertIn("<svg", svg)
        self.assertIn("<rect", svg)

    def test_jalali_conversion(self):
        from core.utils import to_jalali_str
        import datetime

        # ۲۰۲۶-۰۳-۲۱ تقریباً ابتدای بهار = ۱۴۰۵/۰۱/۰۱
        self.assertEqual(to_jalali_str(datetime.date(2026, 3, 21)), "1405/01/01")


class TokenPrintTests(TestCase):
    def test_print_page_has_qr(self):
        admin = User.objects.create_superuser(
            username="p_admin", password="pass12345", role=User.Roles.ADMIN
        )
        person = Personnel.objects.create(
            first_name="چاپ", last_name="آزمون", personnel_code="6001"
        )
        token = issue_token(
            recipient_type=MealToken.RecipientType.PERSONNEL, personnel=person
        )
        self.client.force_login(admin)
        resp = self.client.get(reverse("meals:print", args=[token.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "<svg")
        self.assertContains(resp, token.token_code)
