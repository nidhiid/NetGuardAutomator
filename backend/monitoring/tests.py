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
