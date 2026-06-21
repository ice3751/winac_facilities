from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, ListView

from accounts.models import User
from core.mixins import RoleRequiredMixin

from .forms import DailyMealPlanForm, IssueTokenForm
from .models import DailyMealPlan, MealToken
from .services import MealTokenError, consume_token, issue_token

R = User.Roles
MEAL_ROLES = (R.RESTAURANT, R.RECEPTION)


class IssueTokenView(RoleRequiredMixin, View):
    """صدور ژتون غذا با جلوگیری از تکرار روزانه."""

    allowed_roles = MEAL_ROLES
    template_name = "meals/issue.html"

    def get(self, request):
        return render(request, self.template_name, {"form": IssueTokenForm()})

    def post(self, request):
        form = IssueTokenForm(request.POST)
        if not form.is_valid():
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
            f"ژتون «{token.token_code}» برای «{token.recipient_name}» صادر شد.",
        )
        return redirect("meals:issue")


class ConsumeTokenView(RoleRequiredMixin, View):
    """جستجو و ثبت مصرف ژتون توسط مسئول رستوران."""

    allowed_roles = MEAL_ROLES
    template_name = "meals/consume.html"

    def get_today_tokens(self, query):
        today = timezone.localdate()
        qs = MealToken.objects.filter(date=today).select_related("personnel", "guest")
        if query:
            qs = qs.filter(
                Q(token_code__icontains=query)
                | Q(personnel__first_name__icontains=query)
                | Q(personnel__last_name__icontains=query)
                | Q(guest__first_name__icontains=query)
                | Q(guest__last_name__icontains=query)
            )
        return qs.order_by("status", "-issued_at")

    def get(self, request):
        query = request.GET.get("q", "").strip()
        return render(request, self.template_name, {
            "query": query, "tokens": self.get_today_tokens(query),
        })

    def post(self, request):
        token = get_object_or_404(MealToken, pk=request.POST.get("token_id"))
        try:
            consume_token(token, user=request.user)
        except MealTokenError as exc:
            messages.error(request, str(exc))
        else:
            messages.success(request, f"ژتون «{token.token_code}» مصرف شد.")
        q = request.POST.get("q", "")
        return redirect(f"{reverse_lazy('meals:consume')}?q={q}")


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
