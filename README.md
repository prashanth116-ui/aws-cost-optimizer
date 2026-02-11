# AWS Cost Optimizer

A Python-based tool for analyzing AWS EC2 resource usage and generating rightsizing recommendations with projected cost savings.

## Features

- **Multi-Source Data Collection**: Integrates with Dynatrace, AWS CloudWatch, and AWS Cost Explorer
- **Comprehensive Analysis**: Calculates CPU, memory, and disk usage statistics (avg, p95, etc.)
- **Contention Detection**: Identifies resource bottlenecks and contention events
- **Rightsizing Recommendations**: Generates instance type recommendations with confidence scores
- **Cost Projections**: Calculates potential monthly and yearly savings
- **Cost Anomaly Detection**: Detect unusual spending patterns across AWS services
- **Scheduled Reports**: Automate report generation with email and Slack notifications
- **Multi-Account Support**: Analyze costs across AWS Organizations
- **Excel Reports**: Detailed multi-sheet reports with charts and summaries
- **Interactive Dashboard**: Streamlit-based web dashboard for exploration

## Installation

```bash
cd aws-cost-optimizer
pip install -r requirements.txt
```

## Configuration

1. Copy the credentials template:
   ```bash
   cp config/credentials.template.yaml config/credentials.yaml
   ```

2. Edit `config/credentials.yaml` with your API credentials:

   **Dynatrace:**
   - Get API token from: Settings → Integration → Dynatrace API → Generate token
   - Required scopes: `metrics.read`, `entities.read`, `problems.read`

   **AWS:**
   - Create IAM user with permissions:
     - `ec2:DescribeInstances`
     - `ec2:DescribeInstanceTypes`
     - `ce:GetCostAndUsage`
     - `pricing:GetProducts`
     - `cloudwatch:GetMetricStatistics` (optional)
     - `organizations:ListAccounts` (for multi-account)
     - `sts:AssumeRole` (for multi-account)

## Usage

### Generate Report from CSV Input

```bash
python run.py --input servers.csv --output report.xlsx
```

### Generate Report from AWS Tags

```bash
# Single tag
python run.py --tag GSI MyProject --output report.xlsx

# Multiple tags
python run.py --tag Environment Production --tag Team Platform --output report.xlsx
```

### Launch Interactive Dashboard

```bash
python run.py --dashboard
```

### Cost Anomaly Detection

Detect unusual spending patterns across your AWS services:

```bash
# Run anomaly detection with defaults (30-day baseline, 7-day detection window)
python run.py --detect-anomalies

# Custom baseline and detection periods
python run.py --detect-anomalies --baseline-days 60 --detection-days 14

# Save results to JSON
python run.py --detect-anomalies --output anomalies.json
```

The anomaly detector:
- Builds statistical baselines from historical cost data
- Detects cost spikes and drops using standard deviation thresholds
- Classifies anomalies as warning (2σ) or critical (3σ)
- Groups anomalies by AWS service

### Scheduled Reports

Automate report generation with the scheduler daemon:

```bash
# Start the scheduler daemon
python run.py --daemon

# Run a specific schedule immediately
python run.py --run-schedule weekly-report

# List configured schedules
python run.py --list-schedules
```

Configure schedules in `config/config.yaml`:

```yaml
schedules:
  - id: "weekly-report"
    name: "Weekly Cost Report"
    cron: "0 8 * * MON"  # Every Monday at 8 AM
    report_type: "full"
    recipients:
      - "team@example.com"
    slack_channel: "#cost-alerts"

  - id: "daily-anomalies"
    name: "Daily Anomaly Check"
    cron: "0 9 * * *"  # Every day at 9 AM
    report_type: "anomalies"
    slack_channel: "#cost-alerts"
```

#### Notification Setup

**Email (SMTP):**

Add to `config/config.yaml`:
```yaml
notifications:
  email:
    smtp_host: "smtp.example.com"
    smtp_port: 587
    use_tls: true
    from_address: "cost-optimizer@example.com"
```

Add to `config/credentials.yaml`:
```yaml
notifications:
  email:
    username: "your-smtp-username"
    password: "your-smtp-password"
```

**Slack:**

1. Create a Slack Incoming Webhook at https://api.slack.com/messaging/webhooks
2. Add to `config/config.yaml`:
```yaml
notifications:
  slack:
    default_webhook: "https://hooks.slack.com/services/..."
```

**Test Notifications:**
```bash
python run.py --test-email recipient@example.com
python run.py --test-slack
```

### Multi-Account Analysis

Analyze costs across multiple AWS accounts in your organization:

```bash
# Run multi-account analysis
python run.py --multi-account --output multi_account_report.xlsx

# Validate access to all accounts first
python run.py --validate-multi-account
```

#### Multi-Account Setup

1. **Create IAM Role in Member Accounts**

   Create a role named `CostOptimizerRole` in each member account with this trust policy:

   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Principal": {
           "AWS": "arn:aws:iam::MANAGEMENT_ACCOUNT_ID:root"
         },
         "Action": "sts:AssumeRole"
       }
     ]
   }
   ```

   Attach permissions:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "ec2:DescribeInstances",
           "ec2:DescribeInstanceTypes",
           "ce:GetCostAndUsage",
           "pricing:GetProducts"
         ],
         "Resource": "*"
       }
     ]
   }
   ```

2. **Configure Multi-Account Mode**

   In `config/config.yaml`:
   ```yaml
   organizations:
     enabled: true
     role_name: "CostOptimizerRole"
     # Optional: explicit account list (auto-discovers if empty)
     accounts:
       - account_id: "123456789012"
         name: "Production"
       - account_id: "234567890123"
         name: "Development"
   ```

### Additional Options

```bash
# Specify analysis period (default: 3 months)
python run.py --input servers.csv --months 6 --output report.xlsx

# Use CloudWatch instead of Dynatrace
python run.py --input servers.csv --use-cloudwatch --output report.xlsx

# Test connections only (dry run)
python run.py --dry-run

# Verbose logging
python run.py --input servers.csv --verbose
```

## Input File Format

The CSV/Excel input file should contain server information. The tool auto-detects common column names:

| Column | Alternatives |
|--------|-------------|
| hostname | host, server, server_name, name |
| instance_id | instanceid, instance, ec2_instance |
| ip_address | ip, private_ip |
| gsi | cost_center, project, application |
| environment | env, stage |
| instance_type | type, size |

Example:
```csv
hostname,instance_id,instance_type,gsi,environment
web-server-1,i-12345abc,m5.xlarge,WebApp,Production
db-server-1,i-67890def,r5.2xlarge,Database,Production
```

## Output

### Excel Report Sheets

1. **Executive Summary**: Key metrics, classification breakdown, top savings opportunities
2. **Server Details**: Complete server list with utilization metrics
3. **Recommendations**: Rightsizing recommendations with risk levels
4. **Cost Analysis**: Current vs. optimized spending, savings by GSI
5. **Contention Report**: Servers with resource contention issues
6. **Cost Anomalies**: Detected cost anomalies with baselines (when anomaly detection is run)

### Rightsizing Classifications

| Classification | Criteria | Action |
|---------------|----------|--------|
| **Oversized** | CPU p95 < 40% AND Memory p95 < 50% | Safe to downsize |
| **Right-sized** | CPU p95 40-70% OR Memory p95 50-75% | No change needed |
| **Undersized** | CPU p95 > 80% OR Memory p95 > 85% OR contention | Consider upgrade |

## Dashboard

Launch the Streamlit dashboard for interactive analysis:

```bash
streamlit run dashboard/app.py
# or
python run.py --dashboard
```

### Dashboard Pages

| Page | Description |
|------|-------------|
| Summary | Executive overview with key metrics |
| Server Details | Complete server listing with filters |
| Recommendations | Rightsizing recommendations by risk level |
| Cost Analysis | Spending breakdown and projections |
| What-If Analysis | Scenario modeling for optimization |
| Contention Report | Resource bottleneck analysis |
| **Cost Anomalies** | Unusual spending pattern detection |
| **Schedules** | Manage automated report schedules |
| **Multi-Account** | Cross-account cost analysis |

## Project Structure

```
aws-cost-optimizer/
├── config/
│   ├── config.yaml              # Main configuration
│   ├── credentials.template.yaml # API credentials template
│   └── instance_types.yaml      # AWS instance catalog
├── src/
│   ├── clients/                 # API clients
│   │   ├── aws_client.py
│   │   ├── cloudwatch_client.py
│   │   ├── dynatrace_client.py
│   │   ├── organizations_client.py   # AWS Organizations
│   │   └── multi_account_client.py   # Cross-account orchestration
│   ├── input/                   # Input handlers
│   ├── analysis/                # Analysis engines
│   │   ├── metrics_analyzer.py
│   │   ├── contention_detector.py
│   │   ├── rightsizing.py
│   │   └── anomaly_detector.py       # Cost anomaly detection
│   ├── cost/                    # Cost calculations
│   │   ├── current_spend.py
│   │   ├── projections.py
│   │   └── historical_costs.py       # Historical cost retrieval
│   ├── output/                  # Report generation
│   │   ├── excel_generator.py
│   │   ├── report_data.py
│   │   └── multi_account_report.py   # Multi-account reports
│   ├── scheduler/               # Report scheduling
│   │   ├── scheduler.py              # APScheduler wrapper
│   │   └── daemon.py                 # Background daemon
│   ├── notifications/           # Alerting
│   │   ├── email_sender.py           # SMTP email
│   │   └── slack_notifier.py         # Slack webhooks
│   └── utils/                   # Utilities
├── dashboard/                   # Streamlit dashboard
│   ├── app.py
│   └── pages/
│       ├── 16_anomalies.py           # Anomaly detection page
│       ├── 17_schedules.py           # Schedule management
│       └── 18_multi_account.py       # Multi-account view
├── tests/                       # Unit tests
├── run.py                       # CLI entry point
└── requirements.txt
```

## CLI Reference

| Command | Description |
|---------|-------------|
| `--input FILE` | Input CSV/Excel file with server list |
| `--output FILE` | Output Excel report path |
| `--tag KEY VALUE` | Query AWS by tag (repeatable) |
| `--months N` | Analysis period in months (default: 3) |
| `--region REGION` | AWS region (default: us-east-1) |
| `--dashboard` | Launch Streamlit dashboard |
| `--use-cloudwatch` | Use CloudWatch instead of Dynatrace |
| `--dry-run` | Test connections without generating report |
| `--verbose` | Enable verbose logging |
| `--detect-anomalies` | Run cost anomaly detection |
| `--baseline-days N` | Anomaly baseline period (default: 30) |
| `--detection-days N` | Anomaly detection window (default: 7) |
| `--daemon` | Run scheduler daemon |
| `--run-schedule ID` | Execute specific schedule |
| `--list-schedules` | List configured schedules |
| `--test-email EMAIL` | Send test email |
| `--test-slack` | Send test Slack notification |
| `--multi-account` | Enable multi-account analysis |
| `--validate-multi-account` | Validate access to all accounts |

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test modules
pytest tests/test_anomaly_detector.py -v
pytest tests/test_scheduler.py -v
pytest tests/test_notifications.py -v
pytest tests/test_organizations.py -v
```

## License

MIT License
