#!/usr/bin/env python3
import argparse
import subprocess

from django_bootstrap import setup_django


def run_ping(count, timeout):
    return subprocess.run(
        ["sudo", "ip", "netns", "exec", "client", "ping", "-c", str(count), "-W", str(timeout), "10.0.2.2"],
        capture_output=True,
        text=True,
        check=False,
    )


def main():
    parser = argparse.ArgumentParser(description="Check client-to-server reachability through the firewall namespace.")
    parser.add_argument("--count", type=int, default=3)
    parser.add_argument("--timeout", type=int, default=2)
    args = parser.parse_args()

    setup_django()
    from monitoring.models import SecurityAlert

    result = run_ping(args.count, args.timeout)
    if result.returncode == 0:
        print("HEALTH_CHECK_OK")
        print(result.stdout)
        return 0

    SecurityAlert.objects.create(
        alert_type="HEALTH_CHECK_FAILED",
        severity="HIGH",
        description=f"Client namespace could not reach server namespace.\n\nstdout:\n{result.stdout}\n\nstderr:\n{result.stderr}",
    )
    print("HEALTH_CHECK_FAILED")
    print(result.stderr or result.stdout)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
