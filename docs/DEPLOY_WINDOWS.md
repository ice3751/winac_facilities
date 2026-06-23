# استقرار روی Windows Server (SQL Server + دامنهٔ داخلی HTTP)

راهنمای گام‌به‌گام برای اجرای سامانهٔ ویناک روی VM ویندوزی (مثلاً `DEV`) با
دیتابیس SQL Server و دسترسی داخلی روی HTTP. سرور WSGI: **waitress**، فایل‌های
استاتیک با **WhiteNoise** (نیازی به IIS نیست).

---

## ۰) پیش‌نیازها روی سرور
- دسترسی Administrator به VM ویندوزی.
- یک **SQL Server** در دسترس (روی همین VM یا سرور دیگر) و یک دیتابیس خالی به نام `winac`.
- **ODBC Driver for SQL Server** نصب باشد (Driver 17 یا 18).
- دسترسی شبکه به سرور ایمیل `email.winac-co.com:25`.
- یک رکورد DNS داخلی مثل `winac.intranet.local` که به IP این VM اشاره کند
  (یا فعلاً با IP کار کنید).

## ۱) نصب Python
- از python.org نسخهٔ **3.12** را نصب کنید و گزینهٔ **Add Python to PATH** را بزنید.
- بررسی:
  ```bat
  python --version
  ```

## ۲) نصب درایور SQL Server (در صورت نبود)
- «Microsoft ODBC Driver 17 (یا 18) for SQL Server» را نصب کنید.
- اگر Driver 18 نصب است، در `.env` این را هم بگذارید: `DB_EXTRA_PARAMS=TrustServerCertificate=yes`.

## ۳) گرفتن کد روی سرور
```bat
cd C:\
git clone <repo-url> winac
cd C:\winac
git checkout claude/blissful-hamilton-hki78u
```
> اگر روی سرور Git نیست، می‌توانید پوشهٔ پروژه را به‌صورت ZIP منتقل کنید.

## ۴) محیط مجازی و کتابخانه‌ها
```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install mssql-django pyodbc
```

## ۵) فایل `.env`
```bat
copy .env.production.example .env
notepad .env
```
مقادیر را پر کنید (نمونه در `.env.production.example` هست):
- `SECRET_KEY` یک مقدار تصادفی بلند
- `DEBUG=False`
- `ALLOWED_HOSTS=winac.intranet.local,DEV,<IP سرور>`
- بخش دیتابیس SQL Server: `DB_ENGINE=mssql`, `DB_NAME`, `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_DRIVER`
- بخش ایمیل (همان تنظیمات کارکردهٔ `tashrifat@winac-co.com`)
- `SERVE_PORT=80`

تولید یک SECRET_KEY:
```bat
python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"
```

## ۶) آماده‌سازی دیتابیس و فایل‌ها
```bat
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py setup_roles
python manage.py createsuperuser
```
کاربران واحدها (در صورت نیاز):
```bat
python manage.py create_unit_hosts
```
> ایمیل کاربران را در پنل مدیریت (`/admin/`) با ایمیل واقعی سازمانی پر کنید.

## ۷) تست اجرای دستی
```bat
set SERVE_PORT=80
python serve.py
```
از یک سیستم دیگر در شبکه، مرورگر را باز کنید: `http://winac.intranet.local`
(یا `http://<IP سرور>`). اگر بالا آمد، با `Ctrl+C` متوقف کنید و به مرحلهٔ سرویس بروید.

> اگر پورت ۸۰ اشغال است (IIS)، یا IIS را متوقف کنید یا `SERVE_PORT=8000` بگذارید و
> از `http://winac.intranet.local:8000` استفاده کنید.

## ۸) اجرای دائمی به‌صورت Windows Service (با NSSM)
تا سایت پس از ری‌استارت/خروج هم بالا بماند:

1. **NSSM** را از nssm.cc دانلود و `nssm.exe` را در مسیری مثل `C:\winac\nssm.exe` بگذارید.
2. سرویس را بسازید:
   ```bat
   C:\winac\nssm.exe install WinacWeb
   ```
   در پنجره‌ای که باز می‌شود:
   - **Application Path**: `C:\winac\.venv\Scripts\python.exe`
   - **Startup directory**: `C:\winac`
   - **Arguments**: `serve.py`
   - در تب **Environment** (اختیاری) می‌توانید `SERVE_PORT=80` را بگذارید.
3. شروع سرویس:
   ```bat
   C:\winac\nssm.exe start WinacWeb
   ```
   مدیریت: `nssm restart WinacWeb` / `nssm stop WinacWeb` / در `services.msc`.

## ۹) فایروال
پورت ۸۰ (یا پورتی که انتخاب کردید) را در Windows Firewall باز کنید:
```bat
netsh advfirewall firewall add rule name="Winac HTTP" dir=in action=allow protocol=TCP localport=80
```

## ۱۰) بررسی نهایی
- ورود کاربران از `http://winac.intranet.local`.
- ارسال ایمیل تأییدها کار کند (یک مهمان آزمایشی ثبت/تأیید کنید).
- پنل مدیریت: `http://winac.intranet.local/admin/`.

---

## به‌روزرسانی نسخه (دفعات بعد)
```bat
cd C:\winac
.venv\Scripts\activate
git pull
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
C:\winac\nssm.exe restart WinacWeb
```

## عیب‌یابی سریع
- **خطای اتصال SQL**: `DB_HOST` (نام اینستنس مثل `DEV\SQLEXPRESS`)، باز بودن TCP/IP در
  SQL Server Configuration Manager، و درست بودن درایور/یوزر را بررسی کنید.
- **`Login failed for user`**: یوزر/رمز یا مجوز کاربر روی دیتابیس `winac`.
- **صفحه بدون استایل**: `collectstatic` را اجرا کنید و `DEBUG=False` بماند (WhiteNoise
  استاتیک را سرو می‌کند).
- **`DisallowedHost`**: نام دامنه/آی‌پی را به `ALLOWED_HOSTS` اضافه کنید.
- **CSRF در فرم‌ها**: اگر بعداً HTTPS شد، `CSRF_TRUSTED_ORIGINS=https://winac.intranet.local`.
