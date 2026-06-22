from django import forms

from catering.models import CateringLocation
from core.forms import BootstrapFormMixin
from meals.services import lunch_assignable_for_date

from .models import CardAssignment, Guest, GuestCard


class GuestForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Guest
        fields = [
            "first_name", "last_name", "company", "guest_type", "phone",
            "host_personnel", "visit_date", "expected_entry_time", "expected_exit_time",
            "needs_lunch", "needs_catering", "stationing_location", "status", "description",
        ]
        widgets = {"description": forms.Textarea(attrs={"rows": 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["stationing_location"].queryset = CateringLocation.objects.filter(
            is_active=True
        )

    def clean(self):
        cleaned = super().clean()
        # اگر مهمان نیاز به پذیرایی دارد، محل استقرار (که محل پذیرایی هم می‌شود) الزامی است
        if cleaned.get("needs_catering") and not cleaned.get("stationing_location"):
            self.add_error(
                "stationing_location",
                "برای مهمانی که نیاز به پذیرایی دارد، انتخاب محل استقرار الزامی است "
                "(همین محل، محل پذیرایی او خواهد بود).",
            )
        # تخصیص نهار بعد از ساعت ۱۰ صبحِ روز مراجعهٔ مهمان مجاز نیست
        # (اگر از قبل نهار داشته، ویرایش سایر فیلدها مانعی ندارد)
        already_lunch = bool(self.instance.pk and self.instance.needs_lunch)
        if cleaned.get("needs_lunch") and not already_lunch:
            if not lunch_assignable_for_date(cleaned.get("visit_date")):
                self.add_error(
                    "needs_lunch",
                    "امکان ثبت درخواست نهار برای نهار بعد از ساعت 10 صبح روز مراجعه ی "
                    "مهمان قابل انجام نمیباشد",
                )
        return cleaned


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
