#!/usr/bin/env python3
import argparse
import re
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


def snapshot_to_forward_rules(rendered_config):
    rules = []
    for line in rendered_config.splitlines():
        line = normalize_rule(line)
        if line.startswith(":FORWARD "):
            parts = line.split()
            rules.append(f"-P FORWARD {parts[1]}")
        elif line.startswith("-A FORWARD"):
            rules.append(line)
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

    return [normalize_rule(line) for line in result.stdout.splitlines() if line.strip()]


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

    if expected == current:
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
