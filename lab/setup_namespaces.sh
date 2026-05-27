#!/usr/bin/env bash
set -euo pipefail

CLIENT_NS="client"
FIREWALL_NS="firewall"
SERVER_NS="server"

CLIENT_VETH="veth-client"
FW_CLIENT_VETH="veth-fw1"
SERVER_VETH="veth-server"
FW_SERVER_VETH="veth-fw2"

require_root() {
  if [[ "${EUID}" -ne 0 ]]; then
    echo "Run this script with sudo: sudo ./lab/setup_namespaces.sh" >&2
    exit 1
  fi
}

require_linux_tools() {
  if ! command -v ip >/dev/null 2>&1; then
    echo "Missing 'ip'. Install iproute2 and run on Linux, WSL2, or a Linux VM." >&2
    exit 1
  fi
}

cleanup_existing() {
  ip netns del "${CLIENT_NS}" 2>/dev/null || true
  ip netns del "${FIREWALL_NS}" 2>/dev/null || true
  ip netns del "${SERVER_NS}" 2>/dev/null || true
}

create_namespaces() {
  ip netns add "${CLIENT_NS}"
  ip netns add "${FIREWALL_NS}"
  ip netns add "${SERVER_NS}"
}

create_links() {
  ip link add "${CLIENT_VETH}" type veth peer name "${FW_CLIENT_VETH}"
  ip link set "${CLIENT_VETH}" netns "${CLIENT_NS}"
  ip link set "${FW_CLIENT_VETH}" netns "${FIREWALL_NS}"

  ip link add "${SERVER_VETH}" type veth peer name "${FW_SERVER_VETH}"
  ip link set "${SERVER_VETH}" netns "${SERVER_NS}"
  ip link set "${FW_SERVER_VETH}" netns "${FIREWALL_NS}"
}

configure_interfaces() {
  ip netns exec "${CLIENT_NS}" ip addr add 10.0.1.2/24 dev "${CLIENT_VETH}"
  ip netns exec "${FIREWALL_NS}" ip addr add 10.0.1.1/24 dev "${FW_CLIENT_VETH}"
  ip netns exec "${FIREWALL_NS}" ip addr add 10.0.2.1/24 dev "${FW_SERVER_VETH}"
  ip netns exec "${SERVER_NS}" ip addr add 10.0.2.2/24 dev "${SERVER_VETH}"

  ip netns exec "${CLIENT_NS}" ip link set lo up
  ip netns exec "${FIREWALL_NS}" ip link set lo up
  ip netns exec "${SERVER_NS}" ip link set lo up

  ip netns exec "${CLIENT_NS}" ip link set "${CLIENT_VETH}" up
  ip netns exec "${FIREWALL_NS}" ip link set "${FW_CLIENT_VETH}" up
  ip netns exec "${FIREWALL_NS}" ip link set "${FW_SERVER_VETH}" up
  ip netns exec "${SERVER_NS}" ip link set "${SERVER_VETH}" up
}

configure_routing() {
  ip netns exec "${CLIENT_NS}" ip route add default via 10.0.1.1
  ip netns exec "${SERVER_NS}" ip route add default via 10.0.2.1
  ip netns exec "${FIREWALL_NS}" sysctl -w net.ipv4.ip_forward=1 >/dev/null
}

show_status() {
  echo "Created topology:"
  echo "  client 10.0.1.2/24 -> firewall 10.0.1.1/24"
  echo "  firewall 10.0.2.1/24 -> server 10.0.2.2/24"
  echo
  echo "Test with:"
  echo "  sudo ip netns exec client ping -c 3 10.0.2.2"
}

require_root
require_linux_tools
cleanup_existing
create_namespaces
create_links
configure_interfaces
configure_routing
show_status
