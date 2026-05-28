# Deploy NetGuardAutomator On Oracle Cloud Free VM

This guide deploys the full lab on an Oracle Cloud Ubuntu VM. Use a VM because the project needs Linux network namespaces, `iptables`, Ansible, Docker, and a long-running Django API.

## 1. Create The Oracle Cloud VM

In Oracle Cloud Console:

1. Create an Always Free eligible Ubuntu compute instance.
2. Add your SSH public key.
3. In the VM networking/security list, allow inbound TCP `8000` for the API and TCP `5173` if you want to expose the React dashboard.
4. Keep SSH `22` restricted to your own IP address.

For a public portfolio demo, allow TCP `8000` from `0.0.0.0/0`. For a private demo, restrict TCP `8000` to specific `/32` public IP addresses.

## 2. SSH Into The VM

From your laptop:

```bash
ssh ubuntu@<ORACLE_VM_PUBLIC_IP>
```

## 3. Install System Packages

```bash
sudo apt update
sudo apt install -y \
  git \
  curl \
  python3-venv \
  python3-pip \
  nodejs \
  npm \
  docker.io \
  docker-compose-v2 \
  iproute2 \
  iptables \
  ansible
```

Allow the `ubuntu` user to run Docker:

```bash
sudo usermod -aG docker ubuntu
```

Log out and back in so the Docker group is applied:

```bash
exit
ssh ubuntu@<ORACLE_VM_PUBLIC_IP>
```

Verify:

```bash
docker --version
docker compose version
```

## 4. Clone The Repository

```bash
cd /home/ubuntu
git clone https://github.com/nidhiid/NetGuardAutomator.git
cd NetGuardAutomator
git switch dev
```

## 5. Configure Python And PostgreSQL

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
docker compose up -d postgres
```

Before public demos, edit `.env` and set a non-default API key:

```bash
nano .env
```

Set:

```text
NETGUARD_API_KEY=<long-random-demo-key>
```

Verify PostgreSQL:

```bash
docker compose ps
docker compose exec postgres psql -U netguard -d netguard -c "select current_user, current_database();"
```

The Postgres container uses `restart: unless-stopped`, so Docker should bring it back automatically after VM reboot.

Expected:

```text
 current_user | current_database
--------------+------------------
 netguard     | netguard
```

## 6. Initialize The Django API

```bash
cd /home/ubuntu/NetGuardAutomator/backend
source ../.venv/bin/activate
python manage.py migrate
python manage.py shell -c "from django.conf import settings; print(settings.DATABASES['default']['ENGINE'], settings.DATABASES['default']['PORT'])"
```

Expected:

```text
django.db.backends.postgresql 5433
```

## 7. Install systemd Services

```bash
sudo cp /home/ubuntu/NetGuardAutomator/deploy/systemd/netguard-api.service /etc/systemd/system/
sudo cp /home/ubuntu/NetGuardAutomator/deploy/systemd/netguard-frontend.service /etc/systemd/system/
sudo cp /home/ubuntu/NetGuardAutomator/deploy/systemd/netguard-lab.service /etc/systemd/system/
sudo cp /home/ubuntu/NetGuardAutomator/deploy/systemd/netguard-lab-http.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable netguard-lab
sudo systemctl enable netguard-lab-http
sudo systemctl enable netguard-api
sudo systemctl enable netguard-frontend
sudo systemctl start netguard-lab
sudo systemctl start netguard-lab-http
sudo systemctl start netguard-api
sudo systemctl start netguard-frontend
```

Check service status:

```bash
sudo systemctl status netguard-lab --no-pager
sudo systemctl status netguard-lab-http --no-pager
sudo systemctl status netguard-api --no-pager
sudo systemctl status netguard-frontend --no-pager
```

View service logs:

```bash
journalctl -u netguard-api -f
journalctl -u netguard-frontend -f
journalctl -u netguard-lab-http -f
```

## 8. Verify The Hosted API

From the Oracle VM:

```bash
curl http://127.0.0.1:8000/api/firewall-rules/
```

From your laptop:

```bash
curl http://<ORACLE_VM_PUBLIC_IP>:8000/api/firewall-rules/
```

## 8.1 Run The React Dashboard

The React dashboard is a separate Vite app. Install frontend dependencies once:

```bash
cd /home/ubuntu/NetGuardAutomator/frontend
npm install
sudo systemctl restart netguard-frontend
```

If Oracle ingress allows TCP `5173`, open:

```text
http://<ORACLE_VM_PUBLIC_IP>:5173/
```

The frontend dev server proxies `/api/...` to Django on `127.0.0.1:8000`.

If the laptop curl fails:

1. Confirm the Django service is listening:

   ```bash
   sudo ss -ltnp | grep ':8000'
   ```

2. Confirm Oracle Cloud ingress rules allow TCP `8000`.
3. Confirm Ubuntu firewall is not blocking it:

   ```bash
   sudo ufw status
   ```

## 9. Public Vs Private Access

For a public demo link, use this Oracle Cloud ingress rule:

```text
Source Type: CIDR
Source CIDR: 0.0.0.0/0
IP Protocol: TCP
Destination Port Range: 8000
Stateless: off
Description: NetGuardAutomator public API demo
```

Then share:

```text
http://<ORACLE_VM_PUBLIC_IP>:8000/api/firewall-rules/
```

To make the demo private again, replace the `0.0.0.0/0` source with one or more specific public IPs:

```text
Source CIDR: <trusted_public_ip>/32
Destination Port Range: 8000
```

Find your current public IP:

```bash
curl -4 https://api.ipify.org
```

Keep PostgreSQL private. Do not add public ingress rules for `5432` or `5433`.

Important: public `GET` endpoints are open for portfolio reviewers. Write operations require the `X-NetGuard-API-Key` header configured by `NETGUARD_API_KEY`. Keep that key private.

## 10. Run The Full Demo

On the Oracle VM:

```bash
cd /home/ubuntu/NetGuardAutomator
source .venv/bin/activate
./scripts/demo.sh
```

Expected final line:

```text
==> Demo complete
```

## 11. Install Scheduled Monitoring

The lab can run recurring health, drift, and route checks with systemd timers. These scripts write alerts into PostgreSQL through Django models.

Install the timer units:

```bash
sudo cp /home/ubuntu/NetGuardAutomator/deploy/systemd/netguard-health-check.* /etc/systemd/system/
sudo cp /home/ubuntu/NetGuardAutomator/deploy/systemd/netguard-drift-detector.* /etc/systemd/system/
sudo cp /home/ubuntu/NetGuardAutomator/deploy/systemd/netguard-route-verifier.* /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now netguard-health-check.timer
sudo systemctl enable --now netguard-drift-detector.timer
sudo systemctl enable --now netguard-route-verifier.timer
```

Verify timers are scheduled:

```bash
systemctl list-timers 'netguard-*' --no-pager
```

Run each check immediately:

```bash
sudo systemctl start netguard-health-check.service
sudo systemctl start netguard-drift-detector.service
sudo systemctl start netguard-route-verifier.service
```

Check logs:

```bash
journalctl -u netguard-health-check.service -n 50 --no-pager
journalctl -u netguard-drift-detector.service -n 50 --no-pager
journalctl -u netguard-route-verifier.service -n 50 --no-pager
```

Check alerts through the API:

```bash
curl http://127.0.0.1:8000/api/alerts/ | python -m json.tool
```

If drift or a route mismatch is detected, the related service run can show as failed. That is expected because the monitor exits nonzero when it creates a problem alert.

Stop scheduled monitoring:

```bash
sudo systemctl disable --now netguard-health-check.timer
sudo systemctl disable --now netguard-drift-detector.timer
sudo systemctl disable --now netguard-route-verifier.timer
```

## 12. Restart After Code Changes

```bash
cd /home/ubuntu/NetGuardAutomator
git pull
source .venv/bin/activate
pip install -r requirements.txt
cd backend
python manage.py migrate
sudo systemctl daemon-reload
sudo systemctl restart netguard-lab
sudo systemctl restart netguard-lab-http
docker compose up -d postgres
sudo systemctl restart netguard-api
cd /home/ubuntu/NetGuardAutomator/frontend
npm install
sudo systemctl restart netguard-frontend
```

If timer files changed, restart the timers:

```bash
sudo systemctl restart netguard-health-check.timer
sudo systemctl restart netguard-drift-detector.timer
sudo systemctl restart netguard-route-verifier.timer
```

## 13. Stop Services

```bash
sudo systemctl disable --now netguard-health-check.timer
sudo systemctl disable --now netguard-drift-detector.timer
sudo systemctl disable --now netguard-route-verifier.timer
sudo systemctl stop netguard-frontend
sudo systemctl stop netguard-api
sudo systemctl stop netguard-lab-http
sudo systemctl stop netguard-lab
docker compose down
```

## Notes

- This deployment uses Django's development server for a lab demo. A production deployment should use Gunicorn and Nginx.
- The API runs with development settings. Public `GET` endpoints are open for demos, and write operations require the `X-NetGuard-API-Key` header.
- The lab requires root-level networking commands, so serverless or static hosting platforms are not suitable for the full project.
