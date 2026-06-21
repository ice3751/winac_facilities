"""داشبورد اصلی با کارت‌های آماری و لیست‌های مهم روز جاری."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.views.generic import TemplateView

from catering.models import CateringRequest
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
        return ctx
