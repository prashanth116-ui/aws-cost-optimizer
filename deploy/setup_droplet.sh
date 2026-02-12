#!/bin/bash
# DigitalOcean Deployment Script for AWS Cost Optimizer Dashboard
# Run this ON the droplet after SSH'ing in

set -e

echo "=== AWS Cost Optimizer Dashboard - DigitalOcean Setup ==="

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11+ and pip
sudo apt install -y python3 python3-pip python3-venv git

# Clone or update repo
REPO_DIR="$HOME/aws-cost-optimizer"
if [ -d "$REPO_DIR" ]; then
    echo "Updating existing repo..."
    cd "$REPO_DIR"
    git pull
else
    echo "Cloning repo..."
    git clone https://github.com/prashanth116-ui/aws-cost-optimizer.git "$REPO_DIR"
    cd "$REPO_DIR"
fi

# Create virtual environment
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create directories
mkdir -p config
mkdir -p reports

# Create credentials template if not exists
if [ ! -f "config/credentials.yaml" ]; then
    cp config/credentials.template.yaml config/credentials.yaml
    echo "IMPORTANT: Edit config/credentials.yaml with your AWS credentials"
fi

# Create systemd service for Streamlit
sudo tee /etc/systemd/system/cost-optimizer.service > /dev/null << EOF
[Unit]
Description=AWS Cost Optimizer Dashboard
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$REPO_DIR
Environment="PATH=$REPO_DIR/.venv/bin"
ExecStart=$REPO_DIR/.venv/bin/streamlit run dashboard/app.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable cost-optimizer
sudo systemctl start cost-optimizer

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Dashboard running at: http://$(curl -s ifconfig.me):8501"
echo ""
echo "Commands:"
echo "  View status:  sudo systemctl status cost-optimizer"
echo "  View logs:    sudo journalctl -u cost-optimizer -f"
echo "  Restart:      sudo systemctl restart cost-optimizer"
echo ""
echo "IMPORTANT: Open port 8501 in DigitalOcean firewall!"
echo ""
