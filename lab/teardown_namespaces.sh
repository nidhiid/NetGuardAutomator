#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run this script with sudo: sudo ./lab/teardown_namespaces.sh" >&2
  exit 1
fi

ip netns del client 2>/dev/null || true
ip netns del firewall 2>/dev/null || true
ip netns del server 2>/dev/null || true

echo "Removed lab namespaces."
