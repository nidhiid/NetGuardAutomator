#!/usr/bin/env python3
import argparse
import subprocess
import time

from django_bootstrap import setup_django


def curl_server():
    return subprocess.run(
        ["sudo", "ip", "netns", "exec", "client", "curl", "-s", "--max-time", "2", "http://10.0.2.2/"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )


def main():
    parser = argparse.ArgumentParser(description="Generate client traffic and alert when request volume exceeds a threshold.")
    parser.add_argument("--requests", type=int, default=100)
    parser.add_argument("--sleep", type=float, default=0.01)
    parser.add_argument("--threshold", type=int, default=50)
    parser.add_argument("--auto-block", action="store_true", help="Create a temporary DENY rule and apply it with Ansible.")
    args = parser.parse_args()

    setup_django()
    from configs.services import apply_config_with_ansible
    from monitoring.models import SecurityAlert
    from policies.models import FirewallRule

    successes = 0
    started_at = time.time()

    for _ in range(args.requests):
        result = curl_server()
        if result.returncode == 0:
            successes += 1
        time.sleep(args.sleep)

    elapsed = max(time.time() - started_at, 0.001)
    rate = successes / elapsed

    print(f"requests={args.requests} successes={successes} elapsed={elapsed:.2f}s rate={rate:.2f}/s")

    if successes < args.threshold:
        print("TRAFFIC_WITHIN_THRESHOLD")
        return 0

    description = f"Detected {successes} successful HTTP requests from 10.0.1.2 to 10.0.2.2 in {elapsed:.2f}s."

    if args.auto_block:
        FirewallRule.objects.create(
            source_ip="10.0.1.2",
            destination_ip="10.0.2.2",
            protocol="tcp",
            port=80,
            action=FirewallRule.ACTION_DENY,
            enabled=True,
        )
        result = apply_config_with_ansible()
        description += f"\nAuto-block attempted with Ansible success={result['success']} returncode={result['returncode']}."

    SecurityAlert.objects.create(
        alert_type="SUSPICIOUS_TRAFFIC_VOLUME",
        severity="HIGH",
        description=description,
    )
    print("SUSPICIOUS_TRAFFIC_VOLUME")
    print(description)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
