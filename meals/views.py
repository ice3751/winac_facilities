from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.views import View
from django.views.generic import CreateView, DetailView, ListView

from accounts.models import User
from core.mixins import RoleRequiredMixin

from .forms import DailyMealPlanForm, IssueTokenForm
from .models import DailyMealPlan, MealToken
from .services import (
    MealTokenError,
    issue_token,
    lunch_cutoff_message,
    lunch_window_open,
    mark_printed,
)

R = User.Roles
MEAL_ROLES = (R.RESTAURANT, R.RECEPTION)


class IssueTokenView(RoleRequiredMixin, View):
    """صدور ژتون غذا با جلوگیری از تکرار روزانه و سقف زمانی صبح."""

    allowed_roles = MEAL_ROLES
    template_name = "meals/issue.html"

    def get(self, request):
        return render(request, self.template_name, {
            "form": IssueTokenForm(), "window_open": lunch_window_open(),
            "cutoff_message": lunch_cutoff_message(),
        })

    def post(self, request):
        form = IssueTokenForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})
        # محدودیت زمانی: صدور ژتون نهار فقط تا ساعت ۱۰ صبح
        if not lunch_window_open():
            messages.error(request, lunch_cutoff_message())
            return render(request, self.template_name, {"form": form})
        cd = form.cleaned_data
        try:
            token = issue_token(
                recipient_type=cd["recipient_type"],
                personnel=cd.get("personnel"),
                guest=cd.get("guest"),
                user=request.user,
                description=cd.get("description", ""),
            )
        except MealTokenError as exc:
            messages.error(request, str(exc))
            return render(request, self.template_name, {"form": form})
        messages.success(
            request,
            f"ژتون «{token.token_code}» برای «{token.recipient_name}» صادر شد. "
            "با چاپ، ژتون به‌صورت خودکار مصرف‌شده ثبت می‌شود.",
        )
        # هدایت به صفحهٔ چاپ؛ چاپ = ثبت مصرف
        return redirect("meals:print", pk=token.pk)


class TodayTokensView(RoleRequiredMixin, ListView):
    template_name = "meals/today.html"
    context_object_name = "tokens"
    allowed_roles = MEAL_ROLES

    def get_queryset(self):
        return MealToken.objects.filter(date=timezone.localdate()).select_related(
            "personnel", "guest", "issued_by", "consumed_by"
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = self.get_queryset()
        ctx["count_issued"] = qs.exclude(status=MealToken.Status.CANCELED).count()
        ctx["count_consumed"] = qs.filter(status=MealToken.Status.CONSUMED).count()
        ctx["count_remaining"] = qs.filter(status=MealToken.Status.ISSUED).count()
        return ctx


class TokenPrintView(RoleRequiredMixin, DetailView):
    """صفحهٔ قابل‌چاپ ژتون به همراه QR Code. چاپ = ثبت مصرف خودکار."""

    model = MealToken
    template_name = "meals/print.html"
    context_object_name = "token"
    allowed_roles = MEAL_ROLES

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        # چاپ ژتون به‌منزلهٔ مصرف آن است (بدون نیاز به تأیید مسئول رستوران)
        mark_printed(self.object, user=request.user)
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        from .qr import qr_svg

        ctx = super().get_context_data(**kwargs)
        ctx["qr_svg"] = mark_safe(qr_svg(self.object.token_code))
        return ctx


class DailyMealPlanListView(RoleRequiredMixin, ListView):
    model = DailyMealPlan
    template_name = "meals/plans.html"
    context_object_name = "plans"
    paginate_by = 30
    allowed_roles = MEAL_ROLES


class DailyMealPlanCreateView(RoleRequiredMixin, CreateView):
    model = DailyMealPlan
    form_class = DailyMealPlanForm
    template_name = "crud/form.html"
    success_url = reverse_lazy("meals:plans")
    allowed_roles = MEAL_ROLES

    def get_initial(self):
        return {"date": timezone.localdate()}

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "برنامه نهار روزانه ثبت شد.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "ثبت برنامه نهار روزانه"
        ctx["back_url"] = reverse_lazy("meals:plans")
        return ctx
