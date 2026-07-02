import datetime

from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, ListView, UpdateView

from accounts.models import User
from core.mixins import RoleRequiredMixin

from .forms import CardAssignmentForm, GuestCardForm, GuestForm
from .models import CardAssignment, Guest, GuestCard

R = User.Roles
GUEST_ROLES = (R.RECEPTION, R.HOST)
APPROVAL_ROLES = (R.OFFICE_MANAGER,)


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
        # مدیر واحد (host) فقط مهمان‌های ثبت‌شدهٔ خودش را می‌بیند؛
        # مدیر اداری/سیستم و پذیرش همهٔ مهمان‌ها را می‌بینند.
        if self.request.user.role == R.HOST and not self.request.user.has_full_app_access:
            qs = qs.filter(created_by=self.request.user)
        q = self.request.GET.get("q", "").strip()
        status = self.request.GET.get("status", "").strip()
        visit_date = self.request.GET.get("visit_date", "").strip()
        if q:
            qs = qs.filter(
                Q(first_name__icontains=q) | Q(last_name__icontains=q)
                | Q(company__icontains=q) | Q(phone__icontains=q)
            )
        if status:
            qs = qs.filter(status=status)
        if visit_date:
            try:
                qs = qs.filter(visit_date=datetime.date.fromisoformat(visit_date))
            except ValueError:
                pass
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
        # مدیر اداری/سیستم خود تأییدکننده‌اند؛ ثبتِ مدیر واحد در انتظار تأیید می‌ماند
        if self.request.user.has_role(R.OFFICE_MANAGER):
            form.instance.approval_status = Guest.ApprovalStatus.APPROVED
            form.instance.approved_by = self.request.user
            form.instance.approved_at = timezone.now()
            messages.success(self.request, "مهمان ثبت و تأیید شد.")
        else:
            form.instance.approval_status = Guest.ApprovalStatus.PENDING
            messages.success(
                self.request, "مهمان ثبت شد و برای تأیید به مدیر اداری ارسال گردید."
            )
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
    # مدیر اداری هم می‌تواند مهمان (مثلاً نیاز به نهار/پذیرایی) را پیش از تأیید اصلاح کند
    allowed_roles = (R.RECEPTION, R.HOST, R.OFFICE_MANAGER)

    def get_queryset(self):
        qs = super().get_queryset()
        # مدیر واحد فقط مهمان‌های خودش را می‌تواند ویرایش کند
        if self.request.user.role == R.HOST and not self.request.user.has_full_app_access:
            qs = qs.filter(created_by=self.request.user)
        return qs

    def form_valid(self, form):
        messages.success(self.request, "اطلاعات مهمان به‌روزرسانی شد.")
        return super().form_valid(form)

    def get_success_url(self):
        # مدیر اداری پس از ویرایش به صفحهٔ تأیید بازگردد
        if self.request.user.has_role(R.OFFICE_MANAGER) and not self.request.user.is_admin_role:
            return reverse_lazy("guests:approvals")
        return reverse_lazy("guests:list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "ویرایش مهمان"
        ctx["back_url"] = self.get_success_url()
        return ctx


# --------------------------------------------------------------------------- #
# تأیید مهمان توسط مدیر اداری
# --------------------------------------------------------------------------- #
class GuestApprovalListView(RoleRequiredMixin, ListView):
    """فهرست مهمان‌های در انتظار تأیید برای مدیر اداری."""

    model = Guest
    template_name = "guests/approvals.html"
    context_object_name = "guests"
    paginate_by = 25
    allowed_roles = APPROVAL_ROLES

    def get_queryset(self):
        return (
            super().get_queryset()
            .filter(approval_status=Guest.ApprovalStatus.PENDING)
            .select_related("host_personnel", "created_by")
            .order_by("visit_date")
        )


class GuestReviewView(RoleRequiredMixin, View):
    """تأیید یا رد یک مهمان توسط مدیر اداری."""

    allowed_roles = APPROVAL_ROLES

    def post(self, request, pk):
        guest = get_object_or_404(Guest, pk=pk)
        decision = request.POST.get("decision")
        note = request.POST.get("review_note", "").strip()
        if decision == "approve":
            guest.approval_status = Guest.ApprovalStatus.APPROVED
            messages.success(request, f"مهمان «{guest.full_name}» تأیید شد.")
        elif decision == "reject":
            guest.approval_status = Guest.ApprovalStatus.REJECTED
            messages.warning(request, f"مهمان «{guest.full_name}» رد شد.")
        else:
            messages.error(request, "تصمیم نامعتبر است.")
            return redirect("guests:approvals")
        guest.approved_by = request.user
        guest.approved_at = timezone.now()
        guest.review_note = note
        guest.save(update_fields=[
            "approval_status", "approved_by", "approved_at", "review_note", "updated_at",
        ])
        return redirect("guests:approvals")


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
        initial = {"assigned_date": timezone.localdate(),
                   "delivered_at": timezone.localtime().strftime("%H:%M")}
        guest_id = self.request.GET.get("guest")
        if guest_id:
            initial["guest"] = guest_id
        return initial

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
