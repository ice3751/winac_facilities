from django import forms

from core.forms import BootstrapFormMixin

from .models import Personnel


class PersonnelForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Personnel
        fields = [
            "first_name", "last_name", "personnel_code", "org_unit",
            "person_type", "is_active", "card_id", "description",
        ]
        widgets = {"description": forms.Textarea(attrs={"rows": 2})}
