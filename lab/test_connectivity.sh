#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run this script with sudo: sudo ./lab/test_connectivity.sh" >&2
  exit 1
fi

echo "Pinging server from client..."
ip netns exec client ping -c 3 10.0.2.2

echo
echo "To test HTTP manually:"
echo "  sudo ip netns exec server python3 -m http.server 80"
echo "  sudo ip netns exec client curl http://10.0.2.2/"
