from django.contrib import messages
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from accounts.models import User
from core.mixins import RoleRequiredMixin

from .forms import PersonnelForm
from .models import Personnel

R = User.Roles
PEOPLE_ROLES = (R.RECEPTION, R.RESTAURANT, R.HOST)


class PersonnelListView(RoleRequiredMixin, ListView):
    model = Personnel
    template_name = "people/list.html"
    context_object_name = "people"
    paginate_by = 25
    allowed_roles = PEOPLE_ROLES

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get("q", "").strip()
        ptype = self.request.GET.get("type", "").strip()
        if q:
            qs = qs.filter(
                Q(first_name__icontains=q) | Q(last_name__icontains=q)
                | Q(personnel_code__icontains=q) | Q(org_unit__icontains=q)
            )
        if ptype:
            qs = qs.filter(person_type=ptype)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["type_choices"] = Personnel.PersonType.choices
        return ctx


class PersonnelCreateView(RoleRequiredMixin, CreateView):
    model = Personnel
    form_class = PersonnelForm
    template_name = "crud/form.html"
    success_url = reverse_lazy("people:list")
    allowed_roles = (R.RECEPTION,)

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "پرسنل با موفقیت ثبت شد.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "ثبت پرسنل جدید"
        ctx["back_url"] = reverse_lazy("people:list")
        return ctx


class PersonnelUpdateView(RoleRequiredMixin, UpdateView):
    model = Personnel
    form_class = PersonnelForm
    template_name = "crud/form.html"
    success_url = reverse_lazy("people:list")
    allowed_roles = (R.RECEPTION,)

    def form_valid(self, form):
        messages.success(self.request, "اطلاعات پرسنل به‌روزرسانی شد.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = "ویرایش پرسنل"
        ctx["back_url"] = reverse_lazy("people:list")
        return ctx
