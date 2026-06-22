from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from accounts.models import User
from core.mixins import RoleRequiredMixin

from django.db import transaction

from .forms import (
    CateringItemForm,
    CateringLocationForm,
    CateringRequestForm,
    CateringRequestItemForm,
    CateringRequestItemFormSet,
)
from .models import (
    CateringItem,
    CateringLocation,
    CateringRequest,
    CateringRequestItem,
)

R = User.Roles
CATERING_ROLES = (R.PROTOCOL, R.HOST)
SUPPLY_ROLES = (R.SUPPLY,)
APPROVAL_ROLES = (R.OFFICE_MANAGER,)
# مدیر اداری می‌تواند درخواست تأییدنشده را ویرایش کند
CATERING_EDIT_ROLES = (R.PROTOCOL, R.HOST, R.OFFICE_MANAGER)


# --------------------------------------------------------------------------- #
# اقلام پذیرایی
# --------------------------------------------------------------------------- #
class CateringItemListView(RoleRequiredMixin, ListView):
    model = CateringItem
    template_name = "catering/items.html"
    context_object_name = "items"
    allowed_roles = (R.PROTOCOL,)


class CateringItemCreateView(RoleRequiredMixin, CreateView):
    model = CateringItem
    form_class = CateringItemForm
    template_name = "crud/form.html"
    success_url = reverse_lazy("catering:items")
    allowed_roles = (R.PROTOCOL,)

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "قلم پذیرایی ثبت شد.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "ثبت قلم پذیرایی"
        ctx["back_url"] = reverse_lazy("catering:items")
        return ctx


class CateringItemUpdateView(RoleRequiredMixin, UpdateView):
    model = CateringItem
    form_class = CateringItemForm
    template_name = "crud/form.html"
    success_url = reverse_lazy("catering:items")
    allowed_roles = (R.PROTOCOL,)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "ویرایش قلم پذیرایی"
        ctx["back_url"] = reverse_lazy("catering:items")
        return ctx


# --------------------------------------------------------------------------- #
# درخواست‌های پذیرایی
# --------------------------------------------------------------------------- #
class CateringRequestListView(RoleRequiredMixin, ListView):
    model = CateringRequest
    template_name = "catering/list.html"
    context_object_name = "requests"
    paginate_by = 25
    allowed_roles = CATERING_ROLES

    def get_queryset(self):
        qs = super().get_queryset().select_related("host")
        status = self.request.GET.get("status", "").strip()
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["status_choices"] = CateringRequest.Status.choices
        return ctx


class _CateringRequestFormMixin:
    """منطق مشترک ثبت/ویرایش درخواست پذیرایی همراه با فرم‌ست اقلام."""

    model = CateringRequest
    form_class = CateringRequestForm
    template_name = "catering/form.html"

    def _make_formset(self):
        return CateringRequestItemFormSet(
            self.request.POST or None,
            instance=self.object,
            prefix="items",
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.setdefault("formset", self._make_formset())
        return ctx

    @transaction.atomic
    def _save_all(self, form, formset):
        is_new = form.instance.pk is None
        if is_new:
            form.instance.created_by = self.request.user
            # ثبتِ مدیر اداری/سیستم خودبه‌خود تأیید است؛ بقیه در انتظار تأیید
            if self.request.user.has_role(R.OFFICE_MANAGER):
                form.instance.approval_status = CateringRequest.ApprovalStatus.APPROVED
                form.instance.approved_by = self.request.user
                form.instance.approved_at = timezone.now()
        self.object = form.save()
        formset.instance = self.object
        items = formset.save(commit=False)
        for it in items:
            if it.created_by_id is None:
                it.created_by = self.request.user
            it.save()
        for obj in formset.deleted_objects:
            obj.delete()
        return self.object

    def _handle_post(self, request):
        form = self.get_form()
        formset = CateringRequestItemFormSet(
            request.POST, instance=self.object, prefix="items"
        )
        if form.is_valid() and formset.is_valid():
            self._save_all(form, formset)
            messages.success(request, "درخواست پذیرایی و اقلام آن ذخیره شد.")
            return redirect("catering:detail", pk=self.object.pk)
        return self.render_to_response(self.get_context_data(form=form, formset=formset))


class CateringRequestCreateView(_CateringRequestFormMixin, RoleRequiredMixin, CreateView):
    allowed_roles = CATERING_ROLES

    def get_initial(self):
        return {"catering_date": timezone.localdate()}

    def post(self, request, *args, **kwargs):
        self.object = None
        return self._handle_post(request)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "ثبت درخواست پذیرایی"
        ctx["back_url"] = reverse_lazy("catering:list")
        return ctx


class CateringRequestUpdateView(_CateringRequestFormMixin, RoleRequiredMixin, UpdateView):
    allowed_roles = CATERING_EDIT_ROLES  # شامل مدیر اداری برای اصلاح پیش از تأیید

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return self._handle_post(request)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "ویرایش درخواست پذیرایی"
        ctx["back_url"] = reverse("catering:detail", args=[self.object.pk])
        return ctx


class CateringRequestDetailView(RoleRequiredMixin, DetailView):
    model = CateringRequest
    template_name = "catering/detail.html"
    context_object_name = "req"
    allowed_roles = CATERING_EDIT_ROLES

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["items"] = self.object.items.select_related("item")
        ctx["item_form"] = CateringRequestItemForm()
        ctx["status_choices"] = CateringRequest.Status.choices
        return ctx


class CateringRequestAddItemView(RoleRequiredMixin, View):
    """افزودن یک قلم به درخواست پذیرایی."""

    allowed_roles = CATERING_ROLES

    def post(self, request, pk):
        req = get_object_or_404(CateringRequest, pk=pk)
        form = CateringRequestItemForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.request = req
            obj.created_by = request.user
            obj.save()
            messages.success(request, "قلم به درخواست افزوده شد.")
        else:
            messages.error(request, "اطلاعات قلم نامعتبر است.")
        return redirect("catering:detail", pk=pk)


class CateringRequestDeleteItemView(RoleRequiredMixin, View):
    allowed_roles = CATERING_ROLES

    def post(self, request, pk, item_pk):
        item = get_object_or_404(CateringRequestItem, pk=item_pk, request_id=pk)
        item.delete()
        messages.success(request, "قلم حذف شد.")
        return redirect("catering:detail", pk=pk)


class CateringRequestSetStatusView(RoleRequiredMixin, View):
    """تغییر وضعیت آماده‌سازی/تحویل درخواست پذیرایی."""

    allowed_roles = CATERING_ROLES

    def post(self, request, pk):
        req = get_object_or_404(CateringRequest, pk=pk)
        new_status = request.POST.get("status")
        valid = dict(CateringRequest.Status.choices)
        if new_status in valid:
            req.status = new_status
            req.save(update_fields=["status", "updated_at"])
            messages.success(request, f"وضعیت به «{valid[new_status]}» تغییر کرد.")
        return redirect("catering:detail", pk=pk)


# --------------------------------------------------------------------------- #
# محل‌های پذیرایی
# --------------------------------------------------------------------------- #
class CateringLocationListView(RoleRequiredMixin, ListView):
    model = CateringLocation
    template_name = "catering/locations.html"
    context_object_name = "locations"
    allowed_roles = (R.PROTOCOL,)


class CateringLocationCreateView(RoleRequiredMixin, CreateView):
    model = CateringLocation
    form_class = CateringLocationForm
    template_name = "crud/form.html"
    success_url = reverse_lazy("catering:locations")
    allowed_roles = (R.PROTOCOL,)

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "محل پذیرایی ثبت شد.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "ثبت محل پذیرایی"
        ctx["back_url"] = reverse_lazy("catering:locations")
        return ctx


class CateringLocationUpdateView(RoleRequiredMixin, UpdateView):
    model = CateringLocation
    form_class = CateringLocationForm
    template_name = "crud/form.html"
    success_url = reverse_lazy("catering:locations")
    allowed_roles = (R.PROTOCOL,)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "ویرایش محل پذیرایی"
        ctx["back_url"] = reverse_lazy("catering:locations")
        return ctx


# --------------------------------------------------------------------------- #
# پنل واحد تأمین (اقلام مورد نیاز برای خرید)
# --------------------------------------------------------------------------- #
class SupplyPanelView(RoleRequiredMixin, ListView):
    """فهرست اقلامی که نیاز به خرید دارند، برای واحد تأمین."""

    model = CateringRequestItem
    template_name = "catering/supply.html"
    context_object_name = "items"
    paginate_by = 50
    allowed_roles = SUPPLY_ROLES

    def get_queryset(self):
        qs = (
            CateringRequestItem.objects
            .filter(needs_purchase=True)
            .select_related("item", "request", "request__location")
            .order_by("purchase_status", "request__catering_date")
        )
        show = self.request.GET.get("show", "pending")
        if show == "pending":
            qs = qs.filter(purchase_status=CateringRequestItem.PurchaseStatus.PENDING)
        elif show == "purchased":
            qs = qs.filter(purchase_status=CateringRequestItem.PurchaseStatus.PURCHASED)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["show"] = self.request.GET.get("show", "pending")
        ctx["pending_count"] = CateringRequestItem.objects.filter(
            needs_purchase=True,
            purchase_status=CateringRequestItem.PurchaseStatus.PENDING,
        ).count()
        return ctx


class SupplyMarkPurchasedView(RoleRequiredMixin, View):
    """علامت‌گذاری یک قلم به‌عنوان تهیه‌شده توسط واحد تأمین."""

    allowed_roles = SUPPLY_ROLES

    def post(self, request, item_pk):
        item = get_object_or_404(CateringRequestItem, pk=item_pk, needs_purchase=True)
        if request.POST.get("undo") == "1":
            item.purchase_status = CateringRequestItem.PurchaseStatus.PENDING
            item.purchased_by = None
            item.purchased_at = None
            messages.info(request, "وضعیت تهیه بازگردانده شد.")
        else:
            item.purchase_status = CateringRequestItem.PurchaseStatus.PURCHASED
            item.purchased_by = request.user
            item.purchased_at = timezone.now()
            messages.success(request, f"«{item.item.name}» تهیه‌شده ثبت شد.")
        item.save(update_fields=[
            "purchase_status", "purchased_by", "purchased_at", "updated_at",
        ])
        show = request.POST.get("show", "pending")
        return redirect(f"{reverse('catering:supply')}?show={show}")


# --------------------------------------------------------------------------- #
# تأیید پذیرایی توسط مدیر اداری
# --------------------------------------------------------------------------- #
class CateringApprovalListView(RoleRequiredMixin, ListView):
    """فهرست درخواست‌های پذیرایی در انتظار تأیید برای مدیر اداری."""

    model = CateringRequest
    template_name = "catering/approvals.html"
    context_object_name = "requests"
    paginate_by = 25
    allowed_roles = APPROVAL_ROLES

    def get_queryset(self):
        return (
            super().get_queryset()
            .filter(approval_status=CateringRequest.ApprovalStatus.PENDING)
            .select_related("host", "location", "created_by")
            .order_by("catering_date")
        )


class CateringReviewView(RoleRequiredMixin, View):
    """تأیید یا رد یک درخواست پذیرایی توسط مدیر اداری."""

    allowed_roles = APPROVAL_ROLES

    def post(self, request, pk):
        req = get_object_or_404(CateringRequest, pk=pk)
        decision = request.POST.get("decision")
        note = request.POST.get("review_note", "").strip()
        if decision == "approve":
            req.approval_status = CateringRequest.ApprovalStatus.APPROVED
            messages.success(request, f"پذیرایی «{req.title}» تأیید شد.")
        elif decision == "reject":
            req.approval_status = CateringRequest.ApprovalStatus.REJECTED
            messages.warning(request, f"پذیرایی «{req.title}» رد شد.")
        else:
            messages.error(request, "تصمیم نامعتبر است.")
            return redirect("catering:approvals")
        req.approved_by = request.user
        req.approved_at = timezone.now()
        req.review_note = note
        req.save(update_fields=[
            "approval_status", "approved_by", "approved_at", "review_note", "updated_at",
        ])
        return redirect("catering:approvals")
