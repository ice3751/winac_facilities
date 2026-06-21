"""ابزارهای مشترک فرم‌ها: افزودن خودکار کلاس‌های Bootstrap به ویجت‌ها."""

from django import forms


class BootstrapFormMixin:
    """به همه فیلدهای فرم کلاس مناسب Bootstrap می‌دهد تا قالب‌ها تمیز بمانند."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, (forms.CheckboxInput,)):
                widget.attrs.setdefault("class", "form-check-input")
            elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
                widget.attrs.setdefault("class", "form-select")
            else:
                widget.attrs.setdefault("class", "form-control")
            # ورودی‌های تاریخ/زمان نوع HTML مناسب بگیرند
            if isinstance(widget, forms.DateInput):
                widget.input_type = "date"
                widget.format = "%Y-%m-%d"
            elif isinstance(widget, forms.TimeInput):
                widget.input_type = "time"
                widget.format = "%H:%M"
