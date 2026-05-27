#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run this script with sudo: sudo ./lab/apply_manual_firewall.sh" >&2
  exit 1
fi

if ! ip netns list | awk '{print $1}' | grep -qx "firewall"; then
  echo "Namespace 'firewall' not found. Run sudo ./lab/setup_namespaces.sh first." >&2
  exit 1
fi

IPTABLES="iptables"
if ! ip netns exec firewall sh -c "command -v iptables" >/dev/null 2>&1; then
  echo "Missing iptables inside the firewall namespace." >&2
  exit 1
fi

ip netns exec firewall "${IPTABLES}" -F
ip netns exec firewall "${IPTABLES}" -P FORWARD DROP
ip netns exec firewall "${IPTABLES}" -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
ip netns exec firewall "${IPTABLES}" -A FORWARD -p icmp -s 10.0.1.2 -d 10.0.2.2 -j ACCEPT
ip netns exec firewall "${IPTABLES}" -A FORWARD -p tcp -s 10.0.1.2 -d 10.0.2.2 --dport 80 -j ACCEPT
ip netns exec firewall "${IPTABLES}" -A FORWARD -j DROP

echo "Applied manual firewall policy:"
echo "  allow ICMP client -> server"
echo "  allow HTTP client -> server"
echo "  drop all other forwarded traffic"
