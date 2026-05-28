#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/home/ubuntu/NetGuardAutomator}"
BRANCH="${BRANCH:-main}"

cd "${PROJECT_DIR}"

echo "==> Updating repository"
git fetch origin "${BRANCH}"
git switch "${BRANCH}"
git pull --ff-only origin "${BRANCH}"

echo "==> Starting PostgreSQL"
docker compose up -d postgres

echo "==> Updating Python dependencies and migrations"
source .venv/bin/activate
pip install -r requirements.txt
cd backend
python manage.py migrate
cd ..

echo "==> Updating frontend dependencies"
cd frontend
npm install
cd ..

echo "==> Installing systemd units"
sudo cp deploy/systemd/netguard-*.service /etc/systemd/system/
sudo cp deploy/systemd/netguard-*.timer /etc/systemd/system/ 2>/dev/null || true
sudo systemctl daemon-reload

echo "==> Restarting services"
sudo systemctl restart netguard-lab
sudo systemctl restart netguard-lab-http
sudo systemctl restart netguard-api
sudo systemctl restart netguard-frontend

echo "==> Ensuring monitoring timers are enabled"
sudo systemctl enable --now netguard-health-check.timer
sudo systemctl enable --now netguard-drift-detector.timer
sudo systemctl enable --now netguard-route-verifier.timer

echo "==> Deployment status"
git log --oneline -1
docker compose ps
sudo systemctl --no-pager --full status netguard-api netguard-frontend netguard-lab netguard-lab-http
