import subprocess
from ipaddress import ip_address, ip_network

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
        target = request.query_params.get("target", "10.0.2.2")
        validation_error = validate_lab_target(target)
        if validation_error:
            return Response({"detail": validation_error}, status=400)

        return Response(
            run_lab_command(
                "ping",
                ["sudo", "ip", "netns", "exec", "client", "ping", "-c", "3", "-W", "2", target],
            )
        )


class LabHttpTestView(APIView):
    def get(self, request):
        target = request.query_params.get("target", "10.0.2.2")
        port = request.query_params.get("port", "80")
        validation_error = validate_lab_target(target) or validate_port(port)
        if validation_error:
            return Response({"detail": validation_error}, status=400)

        return Response(
            run_lab_command(
                "http",
                ["sudo", "ip", "netns", "exec", "client", "curl", "--max-time", "3", "-sS", f"http://{target}:{port}/"],
            )
        )


def validate_lab_target(target):
    try:
        parsed = ip_address(target)
    except ValueError:
        return "Target must be an IPv4 address."

    if parsed not in ip_network("10.0.0.0/8"):
        return "Target must be inside the lab 10.0.0.0/8 address range."

    return ""


def validate_port(port):
    try:
        parsed = int(port)
    except ValueError:
        return "Port must be a number."

    if parsed < 1 or parsed > 65535:
        return "Port must be between 1 and 65535."

    return ""


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
