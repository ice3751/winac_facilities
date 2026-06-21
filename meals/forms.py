from django import forms

from core.forms import BootstrapFormMixin
from guests.models import Guest
from people.models import Personnel

from .models import DailyMealPlan, MealToken


class IssueTokenForm(BootstrapFormMixin, forms.Form):
    """فرم صدور ژتون برای پرسنل یا مهمان."""

    recipient_type = forms.ChoiceField(
        label="نوع گیرنده", choices=MealToken.RecipientType.choices
    )
    personnel = forms.ModelChoiceField(
        label="پرسنل", required=False,
        queryset=Personnel.objects.filter(is_active=True),
    )
    guest = forms.ModelChoiceField(
        label="مهمان", required=False,
        queryset=Guest.objects.all(),
    )
    description = forms.CharField(
        label="توضیحات", required=False, widget=forms.Textarea(attrs={"rows": 2})
    )

    def clean(self):
        data = super().clean()
        rtype = data.get("recipient_type")
        if rtype == MealToken.RecipientType.PERSONNEL and not data.get("personnel"):
            self.add_error("personnel", "انتخاب پرسنل الزامی است.")
        if rtype == MealToken.RecipientType.GUEST and not data.get("guest"):
            self.add_error("guest", "انتخاب مهمان الزامی است.")
        return data


class DailyMealPlanForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = DailyMealPlan
        fields = ["date", "expected_personnel", "expected_guests", "total_ordered", "description"]
        widgets = {"description": forms.Textarea(attrs={"rows": 2})}
