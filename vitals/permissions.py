from django.utils import timezone
from rest_framework.permissions import BasePermission
from .models import DeviceToken


class IsIoTDevice(BasePermission):
    """
    Grants access if the request carries a valid X-Device-Key header
    that matches an active DeviceToken row.

    Sets request.device_token so views can read which patient owns this device.
    """
    message = 'Invalid or missing device key. Include X-Device-Key: <token> in your request headers.'

    def has_permission(self, request, view):
        key = request.headers.get('X-Device-Key', '').strip()
        if not key:
            return False
        try:
            token = DeviceToken.objects.select_related('patient__user').get(
                token=key, is_active=True
            )
        except DeviceToken.DoesNotExist:
            return False

        # Attach to request so the view doesn't need to query again
        request.device_token = token

        # Update last_seen in the background (cheap update)
        DeviceToken.objects.filter(pk=token.pk).update(last_seen=timezone.now())
        return True
