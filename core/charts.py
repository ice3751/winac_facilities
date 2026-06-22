"""تولید نمودار میله‌ای ساده به‌صورت SVG در سمت سرور.

بدون هیچ وابستگی JS/CDN، مناسب اجرا روی شبکهٔ داخلی. خروجی یک رشتهٔ SVG است که
مستقیماً در قالب درج می‌شود.
"""

from django.utils.html import escape
from django.utils.safestring import mark_safe


def bar_chart(labels, series, *, width=720, height=240):
    """نمودار میله‌ای گروهی.

    labels: فهرست برچسب محور افقی
    series: فهرست دیکشنری‌هایی به شکل {"values": [...], "cls": "bar-a"}
    """
    pad_l, pad_b, pad_t = 32, 28, 12
    plot_w = width - pad_l - 10
    plot_h = height - pad_b - pad_t

    all_values = [v for s in series for v in s["values"]] or [0]
    max_v = max(all_values) or 1

    n = len(labels) or 1
    group_w = plot_w / n
    k = len(series) or 1
    bar_w = max(4, (group_w * 0.7) / k)

    parts = [
        f'<svg class="svg-chart" viewBox="0 0 {width} {height}" '
        f'xmlns="http://www.w3.org/2000/svg" role="img">'
    ]
    # خط پایه
    base_y = pad_t + plot_h
    parts.append(f'<line x1="{pad_l}" y1="{base_y}" x2="{width-6}" y2="{base_y}" stroke="#d7e3ea"/>')

    for gi, label in enumerate(labels):
        gx = pad_l + gi * group_w + (group_w * 0.15)
        for si, s in enumerate(series):
            val = s["values"][gi] if gi < len(s["values"]) else 0
            bh = (val / max_v) * plot_h
            x = gx + si * bar_w
            y = base_y - bh
            cls = escape(s.get("cls", "bar-a"))
            parts.append(
                f'<rect class="{cls}" x="{x:.1f}" y="{y:.1f}" '
                f'width="{bar_w:.1f}" height="{bh:.1f}" rx="2">'
                f'<title>{escape(str(label))}: {val}</title></rect>'
            )
            if val:
                parts.append(
                    f'<text x="{x + bar_w/2:.1f}" y="{y-3:.1f}" font-size="10" '
                    f'text-anchor="middle" fill="#557">{val}</text>'
                )
        # برچسب محور
        parts.append(
            f'<text x="{gx + (bar_w*k)/2:.1f}" y="{base_y+16:.1f}" font-size="10" '
            f'text-anchor="middle" fill="#667">{escape(str(label))}</text>'
        )

    parts.append("</svg>")
    return mark_safe("".join(parts))
