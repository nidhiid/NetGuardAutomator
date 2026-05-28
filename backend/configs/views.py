from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet

from monitoring.models import SecurityAlert

from .models import ConfigSnapshot
from .serializers import ConfigSnapshotSerializer
from .services import apply_config_with_ansible, render_combined_config, rollback_config_with_ansible


class ConfigSnapshotViewSet(ReadOnlyModelViewSet):
    queryset = ConfigSnapshot.objects.all()
    serializer_class = ConfigSnapshotSerializer


class ApplyConfigView(APIView):
    def post(self, request):
        rendered_config = render_combined_config()
        ansible_result = apply_config_with_ansible()
        snapshot = ConfigSnapshot.objects.create(
            config_type="firewall_and_routes",
            rendered_config=rendered_config,
            applied_successfully=ansible_result["success"],
            ansible_stdout=ansible_result["stdout"],
            ansible_stderr=ansible_result["stderr"],
        )

        if not ansible_result["success"]:
            SecurityAlert.objects.create(
                alert_type="CONFIG_APPLY_FAILED",
                severity="HIGH",
                description=f"Ansible failed while applying snapshot {snapshot.id}.",
            )

        serializer = ConfigSnapshotSerializer(snapshot)
        response_status = status.HTTP_201_CREATED if ansible_result["success"] else status.HTTP_500_INTERNAL_SERVER_ERROR
        return Response(
            {
                "message": "Config applied with Ansible." if ansible_result["success"] else "Config apply failed.",
                "snapshot": serializer.data,
                "ansible": {
                    "success": ansible_result["success"],
                    "returncode": ansible_result["returncode"],
                },
            },
            status=response_status,
        )


class RollbackConfigView(APIView):
    def post(self, request, snapshot_id):
        source_snapshot = get_object_or_404(ConfigSnapshot, id=snapshot_id)
        ansible_result = rollback_config_with_ansible(source_snapshot)
        rollback_snapshot = ConfigSnapshot.objects.create(
            config_type=f"rollback:{source_snapshot.config_type}",
            rendered_config=source_snapshot.rendered_config,
            applied_successfully=ansible_result["success"],
            ansible_stdout=ansible_result["stdout"],
            ansible_stderr=ansible_result["stderr"],
        )
        SecurityAlert.objects.create(
            alert_type="ROLLBACK_APPLIED" if ansible_result["success"] else "ROLLBACK_FAILED",
            severity="MEDIUM" if ansible_result["success"] else "HIGH",
            description=f"Rollback requested using snapshot {source_snapshot.id}; created snapshot {rollback_snapshot.id}.",
        )
        serializer = ConfigSnapshotSerializer(rollback_snapshot)
        response_status = status.HTTP_201_CREATED if ansible_result["success"] else status.HTTP_500_INTERNAL_SERVER_ERROR
        return Response(
            {
                "message": "Rollback applied with Ansible." if ansible_result["success"] else "Rollback failed.",
                "snapshot": serializer.data,
                "ansible": {
                    "success": ansible_result["success"],
                    "returncode": ansible_result["returncode"],
                },
            },
            status=response_status,
        )
