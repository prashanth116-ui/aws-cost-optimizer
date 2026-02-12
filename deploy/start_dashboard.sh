#!/bin/bash
# Start the AWS Cost Optimizer dashboard
cd "$(dirname "$0")/.."
source .venv/bin/activate
streamlit run dashboard/app.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true
