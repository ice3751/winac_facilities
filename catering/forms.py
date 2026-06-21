from django import forms

from core.forms import BootstrapFormMixin

from .models import CateringItem, CateringRequest, CateringRequestItem


class CateringItemForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = CateringItem
        fields = ["name", "unit", "is_active", "description"]
        widgets = {"description": forms.Textarea(attrs={"rows": 2})}


class CateringRequestForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = CateringRequest
        fields = [
            "title", "host", "catering_date", "prepare_time", "location",
            "occasion", "headcount", "status", "description",
        ]
        widgets = {"description": forms.Textarea(attrs={"rows": 2})}


class CateringRequestItemForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = CateringRequestItem
        fields = ["item", "quantity", "description"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["item"].queryset = CateringItem.objects.filter(is_active=True)
