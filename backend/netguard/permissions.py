from django.conf import settings
from rest_framework.permissions import SAFE_METHODS, BasePermission


class ReadOnlyOrApiKey(BasePermission):
    message = "Write operations require a valid X-NetGuard-API-Key header."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        api_key = settings.NETGUARD_API_KEY
        if not api_key:
            return False

        return request.headers.get("X-NetGuard-API-Key") == api_key
