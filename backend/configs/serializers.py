from rest_framework import serializers

from .models import ConfigSnapshot


class ConfigSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfigSnapshot
        fields = [
            "id",
            "config_type",
            "rendered_config",
            "applied_successfully",
            "ansible_stdout",
            "ansible_stderr",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]
