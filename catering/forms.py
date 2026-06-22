from django import forms
from django.db.models import Q
from django.forms import inlineformset_factory

from core.forms import BootstrapFormMixin

from .models import (
    CateringItem,
    CateringLocation,
    CateringRequest,
    CateringRequestItem,
)


class CateringItemForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = CateringItem
        fields = ["name", "unit", "is_active", "description"]
        widgets = {"description": forms.Textarea(attrs={"rows": 2})}


class CateringLocationForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = CateringLocation
        fields = ["name", "capacity", "is_active", "description"]
        widgets = {"description": forms.Textarea(attrs={"rows": 2})}


class CateringRequestForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = CateringRequest
        fields = [
            "title", "host", "catering_date", "location", "start_time", "end_time",
            "prepare_time", "occasion", "headcount", "status", "description",
        ]
        widgets = {"description": forms.Textarea(attrs={"rows": 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["location"].queryset = CateringLocation.objects.filter(is_active=True)

    def clean(self):
        cleaned = super().clean()
        location = cleaned.get("location")
        date = cleaned.get("catering_date")
        start = cleaned.get("start_time")
        end = cleaned.get("end_time")

        if start and end and end <= start:
            self.add_error("end_time", "ساعت پایان باید بعد از ساعت شروع باشد.")
            return cleaned

        # بررسی تداخل رزرو محل در یک بازهٔ زمانی
        if location and date and start and end:
            overlap = (
                CateringRequest.objects
                .filter(location=location, catering_date=date)
                .exclude(status=CateringRequest.Status.CANCELED)
                .filter(start_time__lt=end, end_time__gt=start)
            )
            if self.instance.pk:
                overlap = overlap.exclude(pk=self.instance.pk)
            conflict = overlap.first()
            if conflict:
                self.add_error(
                    "location",
                    f"این محل در تاریخ {date} بین ساعت {conflict.start_time:%H:%M} تا "
                    f"{conflict.end_time:%H:%M} قبلاً برای «{conflict.title}» رزرو شده است.",
                )
        return cleaned


class CateringRequestItemForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = CateringRequestItem
        fields = ["item", "quantity", "needs_purchase", "description"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["item"].queryset = CateringItem.objects.filter(is_active=True)
        self.fields["item"].required = False  # ردیف‌های خالیِ فرم‌ست نادیده گرفته شوند

    def clean(self):
        cleaned = super().clean()
        # اگر ردیف پر شده ولی قلم انتخاب نشده، خطا بده (مگر اینکه حذف شده باشد)
        if self.has_changed() and not cleaned.get("item") and not cleaned.get("DELETE"):
            self.add_error("item", "لطفاً قلم را انتخاب کنید یا ردیف را حذف کنید.")
        return cleaned


# فرم‌ست افزودن چند قلم به‌صورت هم‌زمان داخل فرم درخواست پذیرایی
CateringRequestItemFormSet = inlineformset_factory(
    CateringRequest,
    CateringRequestItem,
    form=CateringRequestItemForm,
    fields=["item", "quantity", "needs_purchase", "description"],
    extra=1,
    can_delete=True,
)
