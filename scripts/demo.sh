#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_BASE_URL="${API_BASE_URL:-http://127.0.0.1:8000}"
HTTP_LOG="${HTTP_LOG:-/tmp/netguard-demo-http.log}"

HTTP_SERVER_PID=""

load_env_file() {
  local env_file="${PROJECT_ROOT}/.env"
  if [[ ! -f "${env_file}" ]]; then
    return
  fi

  set -a
  # shellcheck disable=SC1090
  source "${env_file}"
  set +a
}

cleanup() {
  if [[ -n "${HTTP_SERVER_PID}" ]] && kill -0 "${HTTP_SERVER_PID}" 2>/dev/null; then
    kill "${HTTP_SERVER_PID}" 2>/dev/null || true
  fi
}

trap cleanup EXIT

info() {
  printf "\n==> %s\n" "$1"
}

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

api_check() {
  if ! curl -fsS "${API_BASE_URL}/api/firewall-rules/" >/dev/null; then
    cat >&2 <<EOF
Django API is not reachable at ${API_BASE_URL}.
Start it in another terminal:

  cd ${PROJECT_ROOT}/backend
  source ../.venv/bin/activate
  python manage.py runserver 0.0.0.0:8000
EOF
    exit 1
  fi
}

django_shell() {
  (
    cd "${PROJECT_ROOT}/backend"
    python manage.py shell -c "$1"
  )
}

post_json() {
  local path="$1"
  local body="$2"
  local headers=(-H "Content-Type: application/json")

  if [[ -n "${NETGUARD_API_KEY:-}" ]]; then
    headers+=(-H "X-NetGuard-API-Key: ${NETGUARD_API_KEY}")
  fi

  curl -fsS -X POST "${API_BASE_URL}${path}" \
    "${headers[@]}" \
    -d "${body}" | python -m json.tool
}

latest_snapshot_id() {
  django_shell "from configs.models import ConfigSnapshot; snapshot = ConfigSnapshot.objects.filter(applied_successfully=True).first(); print(snapshot.id if snapshot else '')"
}

require_command curl
require_command python
require_command sudo

cd "${PROJECT_ROOT}"
load_env_file

info "Checking Django API"
api_check

info "Recreating Linux namespace topology"
sudo ./lab/setup_namespaces.sh

info "Starting HTTP server inside server namespace"
sudo ip netns exec server python3 -m http.server 80 >"${HTTP_LOG}" 2>&1 &
HTTP_SERVER_PID="$!"
sleep 1

info "Resetting demo policies and routes"
django_shell "from policies.models import FirewallRule; from routes.models import StaticRoute; FirewallRule.objects.all().delete(); StaticRoute.objects.all().delete(); print('demo policy tables reset')"

info "Creating firewall rules through API"
post_json "/api/firewall-rules/" '{"source_ip":"10.0.1.2","destination_ip":"10.0.2.2","protocol":"icmp","action":"ALLOW","enabled":true}'
post_json "/api/firewall-rules/" '{"source_ip":"10.0.1.2","destination_ip":"10.0.2.2","protocol":"tcp","port":80,"action":"ALLOW","enabled":true}'

info "Creating static route through API"
post_json "/api/routes/" '{"namespace":"client","destination_cidr":"10.0.99.0/24","next_hop":"10.0.1.1"}'

info "Applying API-backed config with Ansible"
post_json "/api/apply-config/" '{}'

info "Verifying firewall rules"
sudo ip netns exec firewall iptables -S FORWARD

info "Verifying route apply"
sudo ip netns exec client ip route show 10.0.99.0/24
python monitor/route_verifier.py

info "Running health check"
python monitor/health_check.py

info "Running drift detector before manual drift"
python monitor/drift_detector.py

info "Injecting manual firewall drift"
sudo ip netns exec firewall iptables -I FORWARD 1 -p tcp --dport 8080 -j ACCEPT
python monitor/drift_detector.py || true

SNAPSHOT_ID="$(latest_snapshot_id | tail -n 1)"
if [[ -z "${SNAPSHOT_ID}" ]]; then
  echo "Could not find a successfully applied snapshot for rollback." >&2
  exit 1
fi

info "Rolling back to snapshot ${SNAPSHOT_ID}"
post_json "/api/rollback/${SNAPSHOT_ID}/" '{}'
python monitor/drift_detector.py

info "Running traffic-volume detector"
python monitor/ddos_detector.py --requests 30 --threshold 10 || true

info "Showing alerts"
curl -fsS "${API_BASE_URL}/api/alerts/" | python -m json.tool

info "Demo complete"
