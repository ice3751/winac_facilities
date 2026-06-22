"""داشبورد اصلی با کارت‌های آماری و لیست‌های مهم روز جاری."""

import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.utils import timezone
from django.views.generic import TemplateView

from catering.models import CateringRequest
from core.charts import bar_chart
from core.utils import to_jalali_str
from guests.models import Guest
from meals.models import DuplicateAttempt, MealToken


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = timezone.localdate()

        tokens_today = MealToken.objects.filter(date=today)
        issued = tokens_today.exclude(status=MealToken.Status.CANCELED)
        consumed = tokens_today.filter(status=MealToken.Status.CONSUMED)
        unconsumed = tokens_today.filter(status=MealToken.Status.ISSUED)

        guests_today = Guest.objects.filter(visit_date=today)
        catering_today = CateringRequest.objects.filter(catering_date=today)
        not_ready = catering_today.filter(
            status__in=[CateringRequest.Status.REGISTERED, CateringRequest.Status.PREPARING]
        )

        ctx.update({
            "stat_guests_today": guests_today.count(),
            "stat_personnel_meals": issued.filter(
                recipient_type=MealToken.RecipientType.PERSONNEL).count(),
            "stat_guest_meals": issued.filter(
                recipient_type=MealToken.RecipientType.GUEST).count(),
            "stat_tokens_issued": issued.count(),
            "stat_tokens_consumed": consumed.count(),
            "stat_tokens_remaining": unconsumed.count(),
            "stat_catering_today": catering_today.count(),
            "stat_catering_not_ready": not_ready.count(),
            "list_guests_today": guests_today.select_related("host_personnel")[:10],
            "list_tokens_issued": issued.select_related("personnel", "guest")[:10],
            "list_tokens_unconsumed": unconsumed.select_related("personnel", "guest")[:10],
            "list_catering_today": catering_today.select_related("host")[:10],
            "list_duplicates": DuplicateAttempt.objects.filter(date=today)[:10],
        })

        # نمودار ۷ روز اخیر: صادرشده در برابر مصرف‌شده
        days = [today - datetime.timedelta(days=i) for i in range(6, -1, -1)]
        agg = {
            r["date"]: r for r in MealToken.objects.filter(date__in=days)
            .values("date")
            .annotate(
                issued=Count("id", filter=~Q(status=MealToken.Status.CANCELED)),
                consumed=Count("id", filter=Q(status=MealToken.Status.CONSUMED)),
            )
        }
        labels = [to_jalali_str(d)[5:] for d in days]  # ماه/روز
        issued_vals = [agg.get(d, {}).get("issued", 0) for d in days]
        consumed_vals = [agg.get(d, {}).get("consumed", 0) for d in days]
        ctx["week_chart"] = bar_chart(labels, [
            {"values": issued_vals, "cls": "bar-b"},
            {"values": consumed_vals, "cls": "bar-a"},
        ])
        return ctx
