from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from .models import StaticRoute


@override_settings(NETGUARD_API_KEY="test-key")
class StaticRouteApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.client.credentials(HTTP_X_NETGUARD_API_KEY="test-key")

    def test_create_static_route(self):
        response = self.client.post(
            "/api/routes/",
            {
                "namespace": "client",
                "destination_cidr": "10.0.99.0/24",
                "next_hop": "10.0.1.1",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            StaticRoute.objects.filter(
                namespace="client",
                destination_cidr="10.0.99.0/24",
                next_hop="10.0.1.1",
            ).exists()
        )
