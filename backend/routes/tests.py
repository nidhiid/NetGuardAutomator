from django.test import TestCase
from rest_framework.test import APIClient

from .models import StaticRoute


class StaticRouteApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

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
