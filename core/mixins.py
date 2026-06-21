"""میکسین‌های کنترل دسترسی مبتنی بر نقش کاربر."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied


class RoleRequiredMixin(LoginRequiredMixin):
    """دسترسی را به نقش‌های مشخص محدود می‌کند.

    کلاس‌های فرزند صفت ``allowed_roles`` را تعیین می‌کنند. مدیر سیستم و superuser
    همیشه دسترسی دارند.
    """

    allowed_roles = ()

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        user = request.user
        if user.is_superuser or user.role == user.Roles.ADMIN:
            return super().dispatch(request, *args, **kwargs)
        if self.allowed_roles and user.role not in self.allowed_roles:
            raise PermissionDenied("شما به این بخش دسترسی ندارید.")
        return super().dispatch(request, *args, **kwargs)
