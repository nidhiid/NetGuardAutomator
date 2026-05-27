#!/usr/bin/env python3
import argparse
from collections import Counter
import re
import shlex
import subprocess

from django_bootstrap import setup_django


def normalize_rule(line):
    line = line.strip()
    line = re.sub(r"\[(\d+):(\d+)\]", "[0:0]", line)
    line = line.replace("/32", "")
    line = line.replace("-m tcp ", "")
    line = line.replace("-m udp ", "")
    line = line.replace("--ctstate RELATED,ESTABLISHED", "--ctstate ESTABLISHED,RELATED")
    return line


def option_value(tokens, option):
    if option not in tokens:
        return ""

    index = tokens.index(option)
    if index + 1 >= len(tokens):
        return ""

    return tokens[index + 1]


def canonical_forward_rule(line):
    line = normalize_rule(line)
    if line.startswith("-P FORWARD"):
        return line
    if not line.startswith("-A FORWARD"):
        return line

    tokens = shlex.split(line)
    protocol = option_value(tokens, "-p")
    source = option_value(tokens, "-s")
    destination = option_value(tokens, "-d")
    destination_port = option_value(tokens, "--dport")
    state = option_value(tokens, "--ctstate")
    action = option_value(tokens, "-j")

    parts = ["-A FORWARD"]
    if state:
        parts.extend(["-m", "conntrack", "--ctstate", state])
    if protocol:
        parts.extend(["-p", protocol])
    if source:
        parts.extend(["-s", source])
    if destination:
        parts.extend(["-d", destination])
    if destination_port:
        parts.extend(["--dport", destination_port])
    if action:
        parts.extend(["-j", action])

    return " ".join(parts)


def snapshot_to_forward_rules(rendered_config):
    rules = []
    for line in rendered_config.splitlines():
        line = normalize_rule(line)
        if line.startswith(":FORWARD "):
            parts = line.split()
            rules.append(canonical_forward_rule(f"-P FORWARD {parts[1]}"))
        elif line.startswith("-A FORWARD"):
            rules.append(canonical_forward_rule(line))
    return rules


def current_forward_rules():
    result = subprocess.run(
        ["sudo", "ip", "netns", "exec", "firewall", "iptables", "-S", "FORWARD"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout)

    return [canonical_forward_rule(line) for line in result.stdout.splitlines() if line.strip()]


def main():
    parser = argparse.ArgumentParser(description="Compare firewall namespace state with the latest applied snapshot.")
    parser.add_argument("--alert-on-missing-snapshot", action="store_true")
    args = parser.parse_args()

    setup_django()
    from configs.models import ConfigSnapshot
    from monitoring.models import SecurityAlert

    snapshot = ConfigSnapshot.objects.filter(applied_successfully=True).first()
    if snapshot is None:
        message = "No successfully applied config snapshot exists."
        if args.alert_on_missing_snapshot:
            SecurityAlert.objects.create(
                alert_type="CONFIG_DRIFT_CHECK_SKIPPED",
                severity="LOW",
                description=message,
            )
        print(message)
        return 0

    expected = snapshot_to_forward_rules(snapshot.rendered_config)
    current = current_forward_rules()

    if Counter(expected) == Counter(current):
        print("NO_CONFIG_DRIFT")
        return 0

    description = "\n".join(
        [
            f"Firewall namespace drift detected against snapshot {snapshot.id}.",
            "",
            "Expected:",
            "\n".join(expected),
            "",
            "Current:",
            "\n".join(current),
        ]
    )
    SecurityAlert.objects.create(
        alert_type="CONFIG_DRIFT_DETECTED",
        severity="HIGH",
        description=description,
    )
    print("CONFIG_DRIFT_DETECTED")
    print(description)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
