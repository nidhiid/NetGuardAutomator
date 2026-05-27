from rest_framework.viewsets import ModelViewSet

from .models import StaticRoute
from .serializers import StaticRouteSerializer


class StaticRouteViewSet(ModelViewSet):
    queryset = StaticRoute.objects.all()
    serializer_class = StaticRouteSerializer
