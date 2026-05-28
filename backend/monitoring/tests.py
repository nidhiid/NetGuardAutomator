from unittest.mock import Mock, patch

from django.test import TestCase
from rest_framework.test import APIClient

from .models import SecurityAlert


class SecurityAlertApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_list_alerts(self):
        SecurityAlert.objects.create(
            alert_type="CONFIG_DRIFT_DETECTED",
            severity="HIGH",
            description="Drift detected.",
        )

        response = self.client.get("/api/alerts/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["alert_type"], "CONFIG_DRIFT_DETECTED")

    @patch("monitoring.views.subprocess.run")
    def test_ping_lab_test_endpoint(self, mock_run):
        mock_run.return_value = Mock(returncode=0, stdout="3 received", stderr="")

        response = self.client.get("/api/lab-tests/ping/")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["test_type"], "ping")

    @patch("monitoring.views.subprocess.run")
    def test_http_lab_test_endpoint_reports_failure(self, mock_run):
        mock_run.return_value = Mock(returncode=28, stdout="", stderr="Connection timed out")

        response = self.client.get("/api/lab-tests/http/")

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["test_type"], "http")
