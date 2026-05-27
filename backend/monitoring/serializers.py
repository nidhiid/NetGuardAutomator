from rest_framework import serializers

from .models import SecurityAlert


class SecurityAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = SecurityAlert
        fields = ["id", "alert_type", "severity", "description", "created_at"]
        read_only_fields = ["id", "created_at"]
