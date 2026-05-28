from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from monitoring.models import SecurityAlert
from policies.models import FirewallRule
from routes.models import StaticRoute

from .models import ConfigSnapshot
from .services import build_ansible_vars, render_combined_config, split_rendered_config


class ConfigRenderingTests(TestCase):
    def test_render_combined_config_includes_firewall_rules_and_routes(self):
        FirewallRule.objects.create(
            source_ip="10.0.1.2",
            destination_ip="10.0.2.2",
            protocol="tcp",
            port=80,
            action=FirewallRule.ACTION_ALLOW,
        )
        StaticRoute.objects.create(
            namespace="client",
            destination_cidr="10.0.99.0/24",
            next_hop="10.0.1.1",
        )

        rendered = render_combined_config()

        self.assertIn("-A FORWARD -p tcp -s 10.0.1.2 -d 10.0.2.2 --dport 80 -j ACCEPT", rendered)
        self.assertIn("# Static routes", rendered)
        self.assertIn("ip netns exec client ip route replace 10.0.99.0/24 via 10.0.1.1", rendered)

    def test_deny_rules_are_ordered_before_allow_rules(self):
        allow_rule = FirewallRule.objects.create(
            source_ip="10.0.1.2",
            destination_ip="10.0.2.2",
            protocol="tcp",
            port=80,
            action=FirewallRule.ACTION_ALLOW,
        )
        deny_rule = FirewallRule.objects.create(
            source_ip="10.0.1.2",
            destination_ip="10.0.2.2",
            protocol="tcp",
            port=80,
            action=FirewallRule.ACTION_DENY,
        )

        rules = build_ansible_vars()["firewall_rules"]
        rule_descriptions = [rule["description"] for rule in rules]

        self.assertLess(rule_descriptions.index(str(deny_rule)), rule_descriptions.index(str(allow_rule)))

    def test_split_rendered_config_separates_firewall_and_route_commands(self):
        rendered_config = "\n".join(
            [
                "*filter",
                ":FORWARD DROP [0:0]",
                "COMMIT",
                "",
                "# Static routes",
                "ip netns exec client ip route replace 10.0.99.0/24 via 10.0.1.1",
            ]
        )

        firewall_config, route_commands = split_rendered_config(rendered_config)

        self.assertEqual(firewall_config, "*filter\n:FORWARD DROP [0:0]\nCOMMIT\n")
        self.assertEqual(
            route_commands,
            ["ip netns exec client ip route replace 10.0.99.0/24 via 10.0.1.1"],
        )


class ConfigApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    @patch("configs.views.apply_config_with_ansible")
    def test_apply_config_creates_successful_snapshot(self, mock_apply):
        mock_apply.return_value = {
            "success": True,
            "returncode": 0,
            "stdout": "ansible ok",
            "stderr": "",
        }
        FirewallRule.objects.create(
            source_ip="10.0.1.2",
            destination_ip="10.0.2.2",
            protocol="icmp",
            action=FirewallRule.ACTION_ALLOW,
        )

        response = self.client.post("/api/apply-config/", {}, format="json")

        self.assertEqual(response.status_code, 201)
        snapshot = ConfigSnapshot.objects.get()
        self.assertTrue(snapshot.applied_successfully)
        self.assertEqual(snapshot.ansible_stdout, "ansible ok")

    @patch("configs.views.apply_config_with_ansible")
    def test_apply_config_failure_creates_alert(self, mock_apply):
        mock_apply.return_value = {
            "success": False,
            "returncode": 2,
            "stdout": "",
            "stderr": "failed",
        }

        response = self.client.post("/api/apply-config/", {}, format="json")

        self.assertEqual(response.status_code, 500)
        self.assertTrue(ConfigSnapshot.objects.filter(applied_successfully=False).exists())
        self.assertTrue(SecurityAlert.objects.filter(alert_type="CONFIG_APPLY_FAILED").exists())

    @patch("configs.views.rollback_config_with_ansible")
    def test_rollback_replays_snapshot_and_creates_alert(self, mock_rollback):
        source_snapshot = ConfigSnapshot.objects.create(
            config_type="firewall_and_routes",
            rendered_config="*filter\nCOMMIT\n",
            applied_successfully=True,
        )
        mock_rollback.return_value = {
            "success": True,
            "returncode": 0,
            "stdout": "rollback ok",
            "stderr": "",
        }

        response = self.client.post(f"/api/rollback/{source_snapshot.id}/", {}, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(ConfigSnapshot.objects.count(), 2)
        rollback_snapshot = ConfigSnapshot.objects.latest("id")
        self.assertEqual(rollback_snapshot.config_type, "rollback:firewall_and_routes")
        self.assertTrue(rollback_snapshot.applied_successfully)
        self.assertTrue(SecurityAlert.objects.filter(alert_type="ROLLBACK_APPLIED").exists())
