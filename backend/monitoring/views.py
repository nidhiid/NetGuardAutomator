from rest_framework.viewsets import ReadOnlyModelViewSet

from .models import SecurityAlert
from .serializers import SecurityAlertSerializer


class SecurityAlertViewSet(ReadOnlyModelViewSet):
    queryset = SecurityAlert.objects.all()
    serializer_class = SecurityAlertSerializer
