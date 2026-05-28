from rest_framework import serializers

from .models import FirewallRule


class FirewallRuleSerializer(serializers.ModelSerializer):
    action = serializers.CharField()

    class Meta:
        model = FirewallRule
        fields = [
            "id",
            "source_ip",
            "destination_ip",
            "protocol",
            "port",
            "action",
            "enabled",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate(self, attrs):
        protocol = attrs.get("protocol", "").lower()
        port = attrs.get("port")

        if protocol:
            attrs["protocol"] = protocol
        if attrs.get("action"):
            attrs["action"] = attrs["action"].upper()
        if attrs.get("action") not in {FirewallRule.ACTION_ALLOW, FirewallRule.ACTION_DENY}:
            raise serializers.ValidationError({"action": "Action must be ALLOW or DENY."})
        if port is not None and protocol not in {"tcp", "udp"}:
            raise serializers.ValidationError({"port": "Port can only be set for tcp or udp rules."})

        return attrs
