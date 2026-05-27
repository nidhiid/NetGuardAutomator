import json
import subprocess
from pathlib import Path

from django.conf import settings

from policies.models import FirewallRule
from routes.models import StaticRoute


def build_ansible_firewall_rule(rule):
    action = "ACCEPT" if rule.action == FirewallRule.ACTION_ALLOW else "DROP"
    protocol = rule.protocol.lower()
    match_parts = []

    if protocol:
        match_parts.extend(["-p", protocol])
    if rule.source_ip:
        match_parts.extend(["-s", rule.source_ip])
    if rule.destination_ip:
        match_parts.extend(["-d", rule.destination_ip])
    if rule.port:
        match_parts.extend(["--dport", str(rule.port)])

    return {
        "description": str(rule),
        "chain": "FORWARD",
        "match": " ".join(match_parts),
        "action": action,
    }


def build_ansible_static_route(route):
    return {
        "namespace": route.namespace,
        "destination_cidr": route.destination_cidr,
        "next_hop": route.next_hop,
    }


def build_ansible_vars():
    firewall_rules = [
        {
            "description": "Allow established return traffic",
            "chain": "FORWARD",
            "match": "-m conntrack --ctstate ESTABLISHED,RELATED",
            "action": "ACCEPT",
        }
    ]
    firewall_rules.extend(
        build_ansible_firewall_rule(rule)
        for rule in FirewallRule.objects.filter(enabled=True).order_by("id")
    )
    firewall_rules.append(
        {
            "description": "Drop all other forwarded traffic",
            "chain": "FORWARD",
            "match": "",
            "action": "DROP",
        }
    )

    return {
        "firewall_namespace": "firewall",
        "firewall_rules": firewall_rules,
        "static_routes": [
            build_ansible_static_route(route)
            for route in StaticRoute.objects.order_by("id")
        ],
    }


def write_ansible_vars_file(ansible_vars):
    runtime_dir = Path(settings.ANSIBLE_RUNTIME_DIR)
    runtime_dir.mkdir(parents=True, exist_ok=True)
    vars_path = runtime_dir / "latest_config.json"
    vars_path.write_text(json.dumps(ansible_vars, indent=2), encoding="utf-8")
    return vars_path


def run_ansible_playbook(playbook_path, vars_path):
    command = [
        "ansible-playbook",
        "-i",
        str(settings.ANSIBLE_INVENTORY),
        str(playbook_path),
        "-e",
        f"@{vars_path}",
    ]

    try:
        result = subprocess.run(
            command,
            cwd=settings.PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        return {
            "success": False,
            "returncode": 127,
            "stdout": "",
            "stderr": f"{exc}. Install Ansible in the active Python environment.",
        }

    return {
        "success": result.returncode == 0,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def apply_config_with_ansible():
    ansible_vars = build_ansible_vars()
    vars_path = write_ansible_vars_file(ansible_vars)
    firewall_result = run_ansible_playbook(settings.ANSIBLE_FIREWALL_PLAYBOOK, vars_path)

    if not firewall_result["success"]:
        return firewall_result

    routes_result = run_ansible_playbook(settings.ANSIBLE_ROUTES_PLAYBOOK, vars_path)
    return {
        "success": routes_result["success"],
        "returncode": routes_result["returncode"],
        "stdout": firewall_result["stdout"] + "\n" + routes_result["stdout"],
        "stderr": firewall_result["stderr"] + "\n" + routes_result["stderr"],
    }


def render_firewall_rule(rule):
    action = "ACCEPT" if rule.action == FirewallRule.ACTION_ALLOW else "DROP"
    protocol = rule.protocol.lower()
    parts = ["-A FORWARD"]

    if protocol:
        parts.extend(["-p", protocol])
    if rule.source_ip:
        parts.extend(["-s", rule.source_ip])
    if rule.destination_ip:
        parts.extend(["-d", rule.destination_ip])
    if rule.port:
        parts.extend(["--dport", str(rule.port)])

    parts.extend(["-j", action])
    return " ".join(parts)


def render_firewall_config():
    lines = [
        "*filter",
        ":INPUT ACCEPT [0:0]",
        ":FORWARD DROP [0:0]",
        ":OUTPUT ACCEPT [0:0]",
        "-A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT",
    ]

    for rule in FirewallRule.objects.filter(enabled=True).order_by("id"):
        lines.append(render_firewall_rule(rule))

    lines.append("-A FORWARD -j DROP")
    lines.append("COMMIT")
    return "\n".join(lines)


def render_routes_config():
    return "\n".join(
        f"ip netns exec {route.namespace} ip route replace {route.destination_cidr} via {route.next_hop}"
        for route in StaticRoute.objects.order_by("id")
    )


def render_combined_config():
    firewall_config = render_firewall_config()
    routes_config = render_routes_config()

    if not routes_config:
        return firewall_config

    return f"{firewall_config}\n\n# Static routes\n{routes_config}"
