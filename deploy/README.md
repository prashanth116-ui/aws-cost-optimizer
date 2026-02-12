# DigitalOcean Deployment

Deploy the AWS Cost Optimizer dashboard to a DigitalOcean droplet.

## Prerequisites

- DigitalOcean account
- SSH key configured
- Git repo pushed to GitHub (update URL in setup_droplet.sh)

## Quick Deploy

### Option 1: Same Droplet as Trading Bot

If using the same droplet, the dashboard will run on port 8501:

```bash
# SSH into your existing droplet
ssh root@YOUR_DROPLET_IP

# Clone and setup
git clone https://github.com/YOUR_USERNAME/aws-cost-optimizer.git
cd aws-cost-optimizer
chmod +x deploy/*.sh
./deploy/setup_droplet.sh
```

### Option 2: New Droplet

1. Create a new droplet ($6/mo Basic is sufficient):
   - Ubuntu 22.04 LTS
   - 1 vCPU, 1GB RAM
   - Enable SSH key

2. SSH in and run setup:
```bash
ssh root@NEW_DROPLET_IP
# Then follow Option 1 steps
```

## Firewall Setup

Open port 8501 in DigitalOcean:
1. Go to Networking → Firewalls
2. Add Inbound Rule: Custom TCP, Port 8501, All IPv4

## Usage

### From Windows (push updates)
```batch
deploy\push_to_server.bat YOUR_DROPLET_IP
```

### On Server
```bash
# View status
sudo systemctl status cost-optimizer

# View logs
./deploy/logs.sh

# Restart
sudo systemctl restart cost-optimizer

# Stop
./deploy/stop_dashboard.sh
```

## Access

Dashboard URL: `http://YOUR_DROPLET_IP:8501`

## AWS Credentials

Edit `config/credentials.yaml` on the server with your AWS credentials for live data:
```yaml
aws:
  access_key_id: "YOUR_KEY"
  secret_access_key: "YOUR_SECRET"
  region: "us-east-1"
```

## Optional: HTTPS with Nginx

For production, add Nginx reverse proxy with SSL:
```bash
sudo apt install nginx certbot python3-certbot-nginx
# Configure domain and SSL certificate
```
