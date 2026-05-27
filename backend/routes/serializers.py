from rest_framework import serializers

from .models import StaticRoute


class StaticRouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaticRoute
        fields = ["id", "namespace", "destination_cidr", "next_hop", "created_at"]
        read_only_fields = ["id", "created_at"]
