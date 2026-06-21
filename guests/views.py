from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, ListView, UpdateView

from accounts.models import User
from core.mixins import RoleRequiredMixin

from .forms import CardAssignmentForm, GuestCardForm, GuestForm
from .models import CardAssignment, Guest, GuestCard

R = User.Roles
GUEST_ROLES = (R.RECEPTION, R.HOST)


# --------------------------------------------------------------------------- #
# مهمان‌ها
# --------------------------------------------------------------------------- #
class GuestListView(RoleRequiredMixin, ListView):
    model = Guest
    template_name = "guests/list.html"
    context_object_name = "guests"
    paginate_by = 25
    allowed_roles = GUEST_ROLES

    def get_queryset(self):
        qs = super().get_queryset().select_related("host_personnel")
        q = self.request.GET.get("q", "").strip()
        status = self.request.GET.get("status", "").strip()
        if q:
            qs = qs.filter(
                Q(first_name__icontains=q) | Q(last_name__icontains=q)
                | Q(company__icontains=q) | Q(phone__icontains=q)
            )
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["status_choices"] = Guest.Status.choices
        return ctx


class GuestCreateView(RoleRequiredMixin, CreateView):
    model = Guest
    form_class = GuestForm
    template_name = "crud/form.html"
    success_url = reverse_lazy("guests:list")
    allowed_roles = GUEST_ROLES

    def get_initial(self):
        return {"visit_date": timezone.localdate()}

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "مهمان با موفقیت ثبت شد.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "ثبت مهمان جدید"
        ctx["back_url"] = reverse_lazy("guests:list")
        return ctx


class GuestUpdateView(RoleRequiredMixin, UpdateView):
    model = Guest
    form_class = GuestForm
    template_name = "crud/form.html"
    success_url = reverse_lazy("guests:list")
    allowed_roles = GUEST_ROLES

    def form_valid(self, form):
        messages.success(self.request, "اطلاعات مهمان به‌روزرسانی شد.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "ویرایش مهمان"
        ctx["back_url"] = reverse_lazy("guests:list")
        return ctx


# --------------------------------------------------------------------------- #
# کارت‌های مهمان
# --------------------------------------------------------------------------- #
class GuestCardListView(RoleRequiredMixin, ListView):
    model = GuestCard
    template_name = "guests/cards.html"
    context_object_name = "cards"
    allowed_roles = GUEST_ROLES


class GuestCardCreateView(RoleRequiredMixin, CreateView):
    model = GuestCard
    form_class = GuestCardForm
    template_name = "crud/form.html"
    success_url = reverse_lazy("guests:cards")
    allowed_roles = GUEST_ROLES

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "کارت مهمان ثبت شد.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "ثبت کارت مهمان"
        ctx["back_url"] = reverse_lazy("guests:cards")
        return ctx


class GuestCardUpdateView(RoleRequiredMixin, UpdateView):
    model = GuestCard
    form_class = GuestCardForm
    template_name = "crud/form.html"
    success_url = reverse_lazy("guests:cards")
    allowed_roles = GUEST_ROLES

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "ویرایش کارت مهمان"
        ctx["back_url"] = reverse_lazy("guests:cards")
        return ctx


# --------------------------------------------------------------------------- #
# تخصیص کارت
# --------------------------------------------------------------------------- #
class CardAssignmentListView(RoleRequiredMixin, ListView):
    model = CardAssignment
    template_name = "guests/assignments.html"
    context_object_name = "assignments"
    paginate_by = 25
    allowed_roles = GUEST_ROLES

    def get_queryset(self):
        return super().get_queryset().select_related("guest", "card", "delivered_by")


class CardAssignmentCreateView(RoleRequiredMixin, CreateView):
    model = CardAssignment
    form_class = CardAssignmentForm
    template_name = "crud/form.html"
    success_url = reverse_lazy("guests:assignments")
    allowed_roles = GUEST_ROLES

    def get_initial(self):
        return {"assigned_date": timezone.localdate(),
                "delivered_at": timezone.localtime().strftime("%H:%M")}

    @transaction.atomic
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.delivered_by = self.request.user
        response = super().form_valid(form)
        # کارت تخصیص‌یافته به وضعیت «تخصیص داده شده» می‌رود
        if self.object.status == CardAssignment.Status.ACTIVE:
            card = self.object.card
            card.status = GuestCard.Status.ASSIGNED
            card.save(update_fields=["status", "updated_at"])
        messages.success(self.request, "کارت به مهمان تخصیص داده شد.")
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "تخصیص کارت به مهمان"
        ctx["back_url"] = reverse_lazy("guests:assignments")
        return ctx


class CardAssignmentUpdateView(RoleRequiredMixin, UpdateView):
    model = CardAssignment
    form_class = CardAssignmentForm
    template_name = "crud/form.html"
    success_url = reverse_lazy("guests:assignments")
    allowed_roles = GUEST_ROLES

    @transaction.atomic
    def form_valid(self, form):
        response = super().form_valid(form)
        # با برگشت/مفقودی کارت، کارت دوباره آزاد می‌شود
        card = self.object.card
        if self.object.status == CardAssignment.Status.ACTIVE:
            card.status = GuestCard.Status.ASSIGNED
        else:
            card.status = GuestCard.Status.FREE
        card.save(update_fields=["status", "updated_at"])
        messages.success(self.request, "تخصیص کارت به‌روزرسانی شد.")
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "ویرایش تخصیص کارت"
        ctx["back_url"] = reverse_lazy("guests:assignments")
        return ctx
