# Deploy NetGuardAutomator On Oracle Cloud Free VM

This guide deploys the full lab on an Oracle Cloud Ubuntu VM. Use a VM because the project needs Linux network namespaces, `iptables`, Ansible, Docker, and a long-running Django API.

## 1. Create The Oracle Cloud VM

In Oracle Cloud Console:

1. Create an Always Free eligible Ubuntu compute instance.
2. Add your SSH public key.
3. In the VM networking/security list, allow inbound TCP `8000`.
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

Verify PostgreSQL:

```bash
docker compose ps
docker compose exec postgres psql -U netguard -d netguard -c "select current_user, current_database();"
```

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
sudo cp /home/ubuntu/NetGuardAutomator/deploy/systemd/netguard-lab.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable netguard-lab
sudo systemctl enable netguard-api
sudo systemctl start netguard-lab
sudo systemctl start netguard-api
```

Check service status:

```bash
sudo systemctl status netguard-lab --no-pager
sudo systemctl status netguard-api --no-pager
```

View API logs:

```bash
journalctl -u netguard-api -f
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

Important: the current API is intentionally open for lab/demo use and includes write endpoints. Public mode is suitable for a short-lived portfolio demo. For a permanent public deployment, add authentication or expose a read-only frontend/reverse proxy.

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

## 11. Restart After Code Changes

```bash
cd /home/ubuntu/NetGuardAutomator
git pull
source .venv/bin/activate
pip install -r requirements.txt
cd backend
python manage.py migrate
sudo systemctl restart netguard-lab
sudo systemctl restart netguard-api
```

## 12. Stop Services

```bash
sudo systemctl stop netguard-api
sudo systemctl stop netguard-lab
docker compose down
```

## Notes

- This deployment uses Django's development server for a lab demo. A production deployment should use Gunicorn and Nginx.
- The API runs with development settings and has unauthenticated write endpoints. Use public ingress only for demos, or add authentication before long-term public exposure.
- The lab requires root-level networking commands, so serverless or static hosting platforms are not suitable for the full project.
