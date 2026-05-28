import subprocess

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet

from .models import SecurityAlert
from .serializers import SecurityAlertSerializer


class SecurityAlertViewSet(ReadOnlyModelViewSet):
    queryset = SecurityAlert.objects.all()
    serializer_class = SecurityAlertSerializer


class LabPingTestView(APIView):
    def get(self, request):
        return Response(
            run_lab_command(
                "ping",
                ["sudo", "ip", "netns", "exec", "client", "ping", "-c", "3", "-W", "2", "10.0.2.2"],
            )
        )


class LabHttpTestView(APIView):
    def get(self, request):
        return Response(
            run_lab_command(
                "http",
                ["sudo", "ip", "netns", "exec", "client", "curl", "--max-time", "3", "-sS", "http://10.0.2.2/"],
            )
        )


def run_lab_command(test_type, command):
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    return {
        "test_type": test_type,
        "success": result.returncode == 0,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "command": " ".join(command),
    }
