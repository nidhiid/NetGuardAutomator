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

        response = self.client.get("/api/lab-tests/ping/?target=10.0.2.2")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["test_type"], "ping")
        self.assertIn("10.0.2.2", response.data["command"])

    @patch("monitoring.views.subprocess.run")
    def test_http_lab_test_endpoint_reports_failure(self, mock_run):
        mock_run.return_value = Mock(returncode=28, stdout="", stderr="Connection timed out")

        response = self.client.get("/api/lab-tests/http/?target=10.0.2.2&port=80")

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["test_type"], "http")
        self.assertIn("http://10.0.2.2:80/", response.data["command"])

    def test_lab_test_rejects_non_lab_target(self):
        response = self.client.get("/api/lab-tests/ping/?target=8.8.8.8")

        self.assertEqual(response.status_code, 400)
