"""اجرای سامانه با waitress (سرور WSGI مناسب ویندوز).

پورت و آدرس از متغیرهای محیطی خوانده می‌شوند:
    SERVE_HOST  (پیش‌فرض 0.0.0.0  → روی همهٔ کارت‌های شبکه)
    SERVE_PORT  (پیش‌فرض 8000)
    SERVE_THREADS (پیش‌فرض 8)

اجرا:
    python serve.py

برای دامنهٔ داخلی روی HTTP بدون وب‌سرور جداگانه، می‌توانید مستقیماً روی پورت ۸۰ گوش دهید:
    set SERVE_PORT=80 && python serve.py
"""

import os

from waitress import serve

from config.wsgi import application

if __name__ == "__main__":
    host = os.getenv("SERVE_HOST", "0.0.0.0")
    port = int(os.getenv("SERVE_PORT", "8000"))
    threads = int(os.getenv("SERVE_THREADS", "8"))
    print(f"Winac running with waitress on http://{host}:{port}  (threads={threads})")
    serve(application, host=host, port=port, threads=threads)
