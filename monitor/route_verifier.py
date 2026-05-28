#!/usr/bin/env python3
import argparse
import subprocess

from django_bootstrap import setup_django


def route_exists(route):
    result = subprocess.run(
        [
            "sudo",
            "ip",
            "netns",
            "exec",
            route.namespace,
            "ip",
            "route",
            "show",
            route.destination_cidr,
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        return False, result.stderr or result.stdout

    expected_via = f"via {route.next_hop}"
    for line in result.stdout.splitlines():
        if line.startswith(route.destination_cidr) and expected_via in line:
            return True, line

    return False, result.stdout


def main():
    parser = argparse.ArgumentParser(description="Verify configured static routes exist inside lab namespaces.")
    parser.add_argument("--alert-on-empty", action="store_true")
    args = parser.parse_args()

    setup_django()
    from monitoring.models import SecurityAlert
    from routes.models import StaticRoute

    routes = list(StaticRoute.objects.order_by("id"))
    if not routes:
        message = "No static routes are configured in the API database."
        if args.alert_on_empty:
            SecurityAlert.objects.create(
                alert_type="ROUTE_VERIFICATION_SKIPPED",
                severity="LOW",
                description=message,
            )
        print(message)
        return 0

    failures = []
    for route in routes:
        exists, output = route_exists(route)
        if exists:
            print(f"OK {route.namespace} {route.destination_cidr} via {route.next_hop}")
        else:
            failures.append((route, output))
            print(f"MISSING {route.namespace} {route.destination_cidr} via {route.next_hop}")

    if not failures:
        print("ROUTE_VERIFICATION_OK")
        return 0

    description_lines = ["Static route verification failed."]
    for route, output in failures:
        description_lines.extend(
            [
                "",
                f"Expected: {route.namespace} {route.destination_cidr} via {route.next_hop}",
                "Observed:",
                output.strip() or "<no route output>",
            ]
        )

    SecurityAlert.objects.create(
        alert_type="ROUTE_APPLY_MISMATCH",
        severity="MEDIUM",
        description="\n".join(description_lines),
    )
    print("ROUTE_APPLY_MISMATCH")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
