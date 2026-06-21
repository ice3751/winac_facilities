"""ویوهای گزارش‌گیری با فیلتر بازه تاریخ و خروجی Excel."""

import datetime

from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views import View

from accounts.models import User
from core.mixins import RoleRequiredMixin

from .reporting import REPORT_TITLES, REPORTS

R = User.Roles
REPORT_ROLES = (R.REPORT_VIEWER,)


def _parse_date(value, default):
    if not value:
        return default
    try:
        return datetime.date.fromisoformat(value)
    except (ValueError, TypeError):
        return default


class ReportIndexView(RoleRequiredMixin, View):
    allowed_roles = REPORT_ROLES

    def get(self, request):
        return render(request, "reports/index.html", {"reports": REPORT_TITLES})


class ReportDetailView(RoleRequiredMixin, View):
    allowed_roles = REPORT_ROLES

    def get(self, request, key):
        func = REPORTS.get(key)
        if func is None:
            raise Http404("گزارش یافت نشد")

        today = timezone.localdate()
        start = _parse_date(request.GET.get("start"), today.replace(day=1))
        end = _parse_date(request.GET.get("end"), today)

        data = func(start, end)

        if request.GET.get("export") == "excel":
            return self._export_excel(key, data, start, end)

        return render(request, "reports/detail.html", {
            "key": key, "data": data, "start": start.isoformat(), "end": end.isoformat(),
        })

    def _export_excel(self, key, data, start, end):
        from openpyxl import Workbook

        wb = Workbook()
        ws = wb.active
        ws.sheet_view.rightToLeft = True
        ws.title = "report"

        ws.append([data["title"]])
        ws.append([f"از {start} تا {end}"])
        ws.append([])
        ws.append(data["headers"])
        for row in data["rows"]:
            ws.append([str(c) if c is not None else "" for c in row])

        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = f'attachment; filename="report_{key}.xlsx"'
        wb.save(response)
        return response
