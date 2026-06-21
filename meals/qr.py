"""تولید QR Code به‌صورت SVG درون‌خطی (بدون نیاز به اینترنت سمت کلاینت).

برای چاپ ژتون استفاده می‌شود؛ خروجی SVG مستقیماً داخل صفحه قرار می‌گیرد تا روی
شبکهٔ داخلی سازمان بدون وابستگی خارجی کار کند.
"""

import qrcode
from qrcode.image.svg import SvgPathImage


def qr_svg(data):
    """یک رشته را به SVG درون‌خطیِ QR تبدیل می‌کند."""
    img = qrcode.make(data, image_factory=SvgPathImage, box_size=10, border=2)
    return img.to_string(encoding="unicode")
