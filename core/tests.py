"""تست‌های دود برای اطمینان از بارگذاری صفحات و قواعد کلیدی ژتون."""

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
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
            "guests:cards", "guests:assignments", "meals:issue", "meals:consume",
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
