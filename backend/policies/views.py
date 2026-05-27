from rest_framework.viewsets import ModelViewSet

from .models import FirewallRule
from .serializers import FirewallRuleSerializer


class FirewallRuleViewSet(ModelViewSet):
    queryset = FirewallRule.objects.all()
    serializer_class = FirewallRuleSerializer
