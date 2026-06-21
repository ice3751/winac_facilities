from django import forms

from core.forms import BootstrapFormMixin

from .models import CardAssignment, Guest, GuestCard


class GuestForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Guest
        fields = [
            "first_name", "last_name", "company", "guest_type", "phone",
            "host_personnel", "visit_date", "expected_entry_time", "expected_exit_time",
            "needs_lunch", "needs_catering", "status", "description",
        ]
        widgets = {"description": forms.Textarea(attrs={"rows": 2})}


class GuestCardForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = GuestCard
        fields = ["title", "card_code", "status", "description"]
        widgets = {"description": forms.Textarea(attrs={"rows": 2})}


class CardAssignmentForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = CardAssignment
        fields = [
            "guest", "card", "assigned_date", "delivered_at", "returned_at",
            "status", "description",
        ]
        widgets = {"description": forms.Textarea(attrs={"rows": 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # فقط کارت‌های آزاد یا کارت فعلیِ همین تخصیص قابل انتخاب باشند
        free = GuestCard.objects.filter(status=GuestCard.Status.FREE)
        if self.instance and self.instance.pk and self.instance.card_id:
            free = free | GuestCard.objects.filter(pk=self.instance.card_id)
        self.fields["card"].queryset = free.distinct()
        # تنها مهمان‌های تأییدشده قابل تخصیص کارت هستند
        self.fields["guest"].queryset = Guest.objects.filter(
            approval_status=Guest.ApprovalStatus.APPROVED
        )
