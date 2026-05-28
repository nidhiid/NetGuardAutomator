from django.test import TestCase
from rest_framework.test import APIClient

from .models import FirewallRule


class FirewallRuleApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_create_firewall_rule_normalizes_action_and_protocol(self):
        response = self.client.post(
            "/api/firewall-rules/",
            {
                "source_ip": "10.0.1.2",
                "destination_ip": "10.0.2.2",
                "protocol": "TCP",
                "port": 80,
                "action": "allow",
                "enabled": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        rule = FirewallRule.objects.get()
        self.assertEqual(rule.protocol, "tcp")
        self.assertEqual(rule.action, FirewallRule.ACTION_ALLOW)

    def test_rejects_port_for_icmp_rule(self):
        response = self.client.post(
            "/api/firewall-rules/",
            {
                "source_ip": "10.0.1.2",
                "destination_ip": "10.0.2.2",
                "protocol": "icmp",
                "port": 80,
                "action": "ALLOW",
                "enabled": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("port", response.data)
