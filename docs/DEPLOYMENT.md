# OpenClass Nexus AI - Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying OpenClass Nexus AI as a Hybrid Orchestrated Edge AI System. The system operates with 100% offline inference at schools, AWS control plane for orchestration, and privacy by architecture design.

**Deployment Model**: One School - One Sovereign AI Node

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Prerequisites](#prerequisites)
3. [Installation Process](#installation-process)
4. [Configuration](#configuration)
5. [Verification](#verification)
6. [Post-Installation Checklist](#post-installation-checklist)
7. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Hardware Requirements

**Minimum Specifications (School Server)**:
- **CPU**: 8-core processor (Intel i7 or AMD Ryzen 7 equivalent)
- **RAM**: 16GB DDR4 (minimum)
- **Storage**: 512GB SSD
- **Network**: 100 Mbps LAN adapter
- **GPU**: Optional (not required, CPU-only inference supported)

**Recommended Specifications**:
- **CPU**: 16-core processor
- **RAM**: 32GB DDR4
- **Storage**: 1TB NVMe SSD
- **Network**: 1 Gbps LAN adapter

**Capacity**:
- Supports 100-300 concurrent students
- Target response latency: 3-8 seconds (90th percentile)
- Maximum 5 concurrent inference threads

### Software Requirements

**Operating System**:
- Ubuntu Server 20.04 LTS or later (recommended)
- Ubuntu Server 22.04 LTS (fully tested)
- Other Linux distributions may work but are not officially supported

**Required Software**:
- Python 3.9 or later (Python 3.11 recommended)
- PostgreSQL 12 or later (PostgreSQL 14 recommended)
- Git 2.25 or later
- systemd (for service management)

**Optional Software**:
- Redis 6.0+ (for enhanced caching, falls back to in-memory LRU cache)
- nginx (for reverse proxy and load balancing)

### Network Requirements

**Local Network**:
- Dedicated school LAN for student/teacher access
- Static IP address for school server (recommended)
- Firewall configured to allow internal LAN access

**Internet Connection** (for initial setup and periodic updates):
- Minimum 10 Mbps download speed
- Required only for:
  - Initial model download (~4GB)
  - Hourly VKP (curriculum) updates
  - Telemetry upload (anonymized metrics only)
- System operates 100% offline after initial setup

---

## Prerequisites

### 1. System Preparation

Update your system and install essential tools:

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install essential build tools
sudo apt install -y build-essential curl wget git
sudo apt install -y software-properties-common
```

### 2. Install Python 3.11

```bash
# Add deadsnakes PPA for Python 3.11
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update

# Install Python 3.11 and development headers
sudo apt install -y python3.11 python3.11-venv python3.11-dev
sudo apt install -y python3-pip

# Verify installation
python3.11 --version  # Should show Python 3.11.x
```

### 3. Install PostgreSQL

```bash
# Install PostgreSQL 14
sudo apt install -y postgresql-14 postgresql-contrib-14

# Start and enable PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Verify installation
sudo systemctl status postgresql
```

### 4. Create Application User

```bash
# Create dedicated user for OpenClass Nexus AI
sudo useradd -m -s /bin/bash nexusai
sudo usermod -aG sudo nexusai  # Optional: grant sudo access

# Create application directory
sudo mkdir -p /opt/nexusai
sudo chown nexusai:nexusai /opt/nexusai
```

---

## Installation Process

### Step 1: Download Deployment Package

```bash
# Switch to application user
sudo su - nexusai

# Navigate to application directory
cd /opt/nexusai

# Clone repository (or extract deployment package)
git clone https://github.com/your-org/openclass-nexus-ai.git .

# Alternatively, if using deployment package:
# tar -xzf openclass-nexus-deployment.tar.gz -C /opt/nexusai
```

### Step 2: Run Automated Installer

The deployment package includes an automated installer script that handles all setup tasks.

```bash
# Make installer executable
chmod +x install.sh

# Run installer (interactive mode)
./install.sh

# Or run in unattended mode with defaults
./install.sh --unattended
```

The installer performs the following tasks:
1. ✓ Checks system requirements (CPU, RAM, disk space)
2. ✓ Installs Python dependencies from requirements.txt
3. ✓ Configures PostgreSQL database and creates schema
4. ✓ Downloads LLM model (Llama 3.2 3B quantized, ~4GB)
5. ✓ Initializes ChromaDB vector database
6. ✓ Creates admin user account
7. ✓ Configures systemd services for auto-start
8. ✓ Verifies installation and starts services

**Installation Time**: Approximately 15-30 minutes (depending on internet speed for model download)

### Step 3: Manual Installation (Alternative)

If you prefer manual installation or the automated installer fails, follow these steps:

#### 3.1 Create Python Virtual Environment

```bash
cd /opt/nexusai

# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel
```

#### 3.2 Install Python Dependencies

```bash
# Install all required packages
pip install -r requirements.txt

# Verify critical packages
pip list | grep -E "fastapi|uvicorn|psycopg2|chromadb|llama-cpp-python"
```

#### 3.3 Configure PostgreSQL Database

```bash
# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE nexusai_db;
CREATE USER nexusai_user WITH ENCRYPTED PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE nexusai_db TO nexusai_user;
\q
EOF

# Initialize database schema
python scripts/setup_database.py --init-schema

# Verify database connection
python scripts/check_database.py
```

#### 3.4 Download LLM Model

```bash
# Download Llama 3.2 3B quantized model (Q4_K_M)
python scripts/download_model.py --model llama-3.2-3b-instruct-q4_k_m

# Verify model integrity
python scripts/verify_model.py

# Model location: /opt/nexusai/models/llama-3.2-3b-instruct-q4_k_m.gguf
```

#### 3.5 Initialize ChromaDB

```bash
# Create ChromaDB directory
mkdir -p /opt/nexusai/data/vector_db

# Initialize ChromaDB collections
python scripts/setup_chromadb.py --init-collections

# Verify ChromaDB
python scripts/check_chromadb.py
```

#### 3.6 Create Admin User

```bash
# Create admin account (interactive)
python scripts/create_admin.py

# Or create with command-line arguments
python scripts/create_admin.py \
  --username admin \
  --password "SecurePassword123!" \
  --full-name "System Administrator" \
  --role admin
```

---

## Configuration

### 1. Environment Configuration

Create and configure the environment file:

```bash
# Copy example configuration
cp .env.example .env

# Edit configuration
nano .env
```

**Key Configuration Parameters**:

```bash
# Database Configuration
DATABASE_URL=postgresql://nexusai_user:your_secure_password@localhost:5432/nexusai_db
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Model Configuration
MODEL_PATH=/opt/nexusai/models/llama-3.2-3b-instruct-q4_k_m.gguf
MODEL_CONTEXT_LENGTH=4096
MODEL_N_THREADS=8
MODEL_MAX_TOKENS=512

# Concurrency Configuration
MAX_CONCURRENT_INFERENCE=5
MAX_QUEUE_SIZE=1000

# ChromaDB Configuration
CHROMADB_PATH=/opt/nexusai/data/vector_db
CHROMADB_COLLECTION_NAME=curriculum_embeddings

# Embedding Strategy (bedrock or local)
EMBEDDING_STRATEGY=bedrock
EMBEDDING_FALLBACK_TO_LOCAL=true

# AWS Configuration (for VKP updates and telemetry)
AWS_REGION=ap-southeast-1
AWS_S3_VKP_BUCKET=nexusai-vkp-packages
AWS_DYNAMODB_METRICS_TABLE=nexusai-metrics

# School Configuration
SCHOOL_ID=your_school_id
SCHOOL_NAME="Your School Name"

# Telemetry Configuration
TELEMETRY_ENABLED=true
TELEMETRY_UPLOAD_INTERVAL_HOURS=1
TELEMETRY_ANONYMIZE_SCHOOL_ID=true

# VKP Pull Configuration
VKP_PULL_ENABLED=true
VKP_PULL_INTERVAL_HOURS=1

# Caching Configuration (optional)
REDIS_URL=redis://localhost:6379/0
CACHE_TTL_SECONDS=86400
CACHE_FALLBACK_TO_LRU=true

# Backup Configuration
BACKUP_ENABLED=true
BACKUP_WEEKLY_FULL=true
BACKUP_DAILY_INCREMENTAL=true
BACKUP_RETENTION_DAYS=28

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=/var/log/nexusai/app.log
```

### 2. Systemd Service Configuration

The installer creates systemd services automatically. To configure manually:

#### 2.1 Main API Service

Create `/etc/systemd/system/nexusai-api.service`:

```ini
[Unit]
Description=OpenClass Nexus AI API Service
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=nexusai
Group=nexusai
WorkingDirectory=/opt/nexusai
Environment=PATH=/opt/nexusai/venv/bin
EnvironmentFile=/opt/nexusai/.env
ExecStart=/opt/nexusai/venv/bin/python src/api/server.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Resource limits
LimitNOFILE=65536
MemoryLimit=14G

[Install]
WantedBy=multi-user.target
```

#### 2.2 Health Monitor Service

Create `/etc/systemd/system/nexusai-health-monitor.service`:

```ini
[Unit]
Description=OpenClass Nexus AI Health Monitor
After=nexusai-api.service
Requires=nexusai-api.service

[Service]
Type=simple
User=nexusai
Group=nexusai
WorkingDirectory=/opt/nexusai
Environment=PATH=/opt/nexusai/venv/bin
EnvironmentFile=/opt/nexusai/.env
ExecStart=/opt/nexusai/venv/bin/python src/resilience/health_monitor_daemon.py
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

#### 2.3 Enable and Start Services

```bash
# Reload systemd daemon
sudo systemctl daemon-reload

# Enable services (start on boot)
sudo systemctl enable nexusai-api
sudo systemctl enable nexusai-health-monitor

# Start services
sudo systemctl start nexusai-api
sudo systemctl start nexusai-health-monitor

# Check service status
sudo systemctl status nexusai-api
sudo systemctl status nexusai-health-monitor
```

### 3. Cron Jobs Configuration

Configure periodic tasks for VKP updates, telemetry, and backups:

```bash
# Edit crontab for nexusai user
sudo -u nexusai crontab -e
```

Add the following cron jobs:

```cron
# VKP Pull (hourly at minute 0)
0 * * * * /opt/nexusai/venv/bin/python /opt/nexusai/src/aws_control_plane/vkp_puller.py >> /var/log/nexusai/vkp_pull.log 2>&1

# Telemetry Upload (hourly at minute 30)
30 * * * * /opt/nexusai/venv/bin/python /opt/nexusai/src/telemetry/telemetry_uploader.py >> /var/log/nexusai/telemetry.log 2>&1

# Weekly Full Backup (Sunday at 2:00 AM)
0 2 * * 0 /opt/nexusai/venv/bin/python /opt/nexusai/src/resilience/backup_scheduler.py --full >> /var/log/nexusai/backup.log 2>&1

# Daily Incremental Backup (Monday-Saturday at 2:00 AM)
0 2 * * 1-6 /opt/nexusai/venv/bin/python /opt/nexusai/src/resilience/backup_scheduler.py --incremental >> /var/log/nexusai/backup.log 2>&1

# Cleanup Expired Sessions (daily at 3:00 AM)
0 3 * * * /opt/nexusai/venv/bin/python /opt/nexusai/scripts/cleanup_sessions.py >> /var/log/nexusai/cleanup.log 2>&1
```

### 4. Firewall Configuration

Configure firewall to allow internal LAN access:

```bash
# Install UFW (if not already installed)
sudo apt install -y ufw

# Allow SSH (important!)
sudo ufw allow 22/tcp

# Allow API access from LAN only (adjust subnet as needed)
sudo ufw allow from 192.168.1.0/24 to any port 8000 proto tcp

# Enable firewall
sudo ufw enable

# Check firewall status
sudo ufw status verbose
```

---

## Verification

### 1. System Health Check

Run comprehensive system verification:

```bash
# Activate virtual environment
cd /opt/nexusai
source venv/bin/activate

# Run system health check
python scripts/check_system_health.py

# Expected output:
# ✓ Python version: 3.11.x
# ✓ PostgreSQL connection: OK
# ✓ ChromaDB connection: OK
# ✓ LLM model loaded: OK
# ✓ Disk space: 450GB available (88%)
# ✓ RAM usage: 4.2GB / 16GB (26%)
# ✓ API service: Running
# ✓ Health monitor: Running
```

### 2. API Endpoint Verification

Test API endpoints:

```bash
# Health check endpoint
curl http://localhost:8000/health

# Expected response:
# {
#   "status": "healthy",
#   "model_loaded": true,
#   "database_ready": true,
#   "chromadb_ready": true,
#   "memory_usage_mb": 4200,
#   "uptime_seconds": 120
# }

# Test authentication
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your_password"}'

# Expected response:
# {
#   "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
#   "token_type": "bearer",
#   "expires_in": 86400
# }
```

### 3. Test Query Processing

Submit a test query:

```bash
# Get access token first
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your_password"}' \
  | jq -r '.access_token')

# Submit test query
curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Apa itu teorema Pythagoras?",
    "subject_id": 1
  }'

# Expected: Streaming response with educational content
```

### 4. Database Verification

Verify database schema and data:

```bash
# Connect to PostgreSQL
sudo -u postgres psql nexusai_db

# Check tables
\dt

# Expected tables:
# users, sessions, chat_history, subjects, books,
# topic_mastery, weak_areas, practice_questions,
# vkp_versions, telemetry_queue

# Check admin user
SELECT username, role, full_name FROM users WHERE role = 'admin';

# Exit PostgreSQL
\q
```

### 5. ChromaDB Verification

Verify vector database:

```bash
# Check ChromaDB collections
python scripts/check_chromadb.py --list-collections

# Expected output:
# Collections:
#   - curriculum_embeddings (0 documents)
#   - practice_questions (0 documents)

# Note: Collections will be empty until first VKP update
```

### 6. Log Verification

Check application logs:

```bash
# View API service logs
sudo journalctl -u nexusai-api -n 50 --no-pager

# View health monitor logs
sudo journalctl -u nexusai-health-monitor -n 50 --no-pager

# View application log file
tail -f /var/log/nexusai/app.log
```

---

## Post-Installation Checklist

Complete the following checklist after installation:

### Essential Tasks

- [ ] **System Requirements Met**
  - [ ] 16GB RAM minimum
  - [ ] 8-core CPU
  - [ ] 512GB SSD storage
  - [ ] Ubuntu Server 20.04 LTS or later

- [ ] **Software Installed**
  - [ ] Python 3.11 installed and verified
  - [ ] PostgreSQL 12+ installed and running
  - [ ] All Python dependencies installed
  - [ ] LLM model downloaded and verified

- [ ] **Database Configuration**
  - [ ] PostgreSQL database created
  - [ ] Database schema initialized
  - [ ] Admin user created
  - [ ] Database connection verified

- [ ] **Services Running**
  - [ ] nexusai-api service running
  - [ ] nexusai-health-monitor service running
  - [ ] Services enabled for auto-start
  - [ ] Service logs show no errors

- [ ] **API Verification**
  - [ ] Health endpoint responds correctly
  - [ ] Authentication works
  - [ ] Test query processes successfully
  - [ ] Response time within 3-8 seconds

- [ ] **Network Configuration**
  - [ ] Firewall configured for LAN access
  - [ ] Static IP assigned (recommended)
  - [ ] Students can access from LAN
  - [ ] Internet connectivity verified

### Optional Tasks

- [ ] **AWS Integration** (if using cloud features)
  - [ ] AWS credentials configured
  - [ ] S3 bucket access verified
  - [ ] VKP pull mechanism tested
  - [ ] Telemetry upload verified

- [ ] **Caching Layer** (if using Redis)
  - [ ] Redis installed and running
  - [ ] Cache connection verified
  - [ ] Cache hit/miss metrics working

- [ ] **Backup System**
  - [ ] Backup directory created
  - [ ] Backup cron jobs configured
  - [ ] Test backup created and verified
  - [ ] Restore procedure tested

- [ ] **Monitoring** (if using external monitoring)
  - [ ] Prometheus metrics endpoint configured
  - [ ] Grafana dashboards imported
  - [ ] Alert rules configured

### Documentation Tasks

- [ ] **Record Configuration**
  - [ ] Document server IP address
  - [ ] Document admin credentials (secure storage)
  - [ ] Document database credentials (secure storage)
  - [ ] Document AWS credentials (if applicable)

- [ ] **User Training**
  - [ ] Train teachers on system usage
  - [ ] Provide student access instructions
  - [ ] Document common troubleshooting steps
  - [ ] Establish support contact

---

## Troubleshooting

### Common Issues and Solutions

#### Issue 1: Installation Fails - Insufficient RAM

**Symptom**: Installer reports "Insufficient RAM: 8GB detected, 16GB required"

**Solution**:
```bash
# Check actual RAM
free -h

# If RAM is insufficient, upgrade hardware
# Minimum 16GB RAM is required for stable operation with 100-300 concurrent users
```

#### Issue 2: PostgreSQL Connection Failed

**Symptom**: `psycopg2.OperationalError: could not connect to server`

**Solution**:
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# If not running, start it
sudo systemctl start postgresql

# Check PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-14-main.log

# Verify connection settings in .env file
# Ensure DATABASE_URL is correct
```

#### Issue 3: Model Download Fails

**Symptom**: "Failed to download model: Connection timeout"

**Solution**:
```bash
# Check internet connectivity
ping -c 4 8.8.8.8

# Try manual download with resume support
wget -c https://huggingface.co/TheBloke/Llama-3.2-3B-Instruct-GGUF/resolve/main/llama-3.2-3b-instruct-q4_k_m.gguf \
  -O /opt/nexusai/models/llama-3.2-3b-instruct-q4_k_m.gguf

# Verify model integrity
python scripts/verify_model.py
```

#### Issue 4: API Service Won't Start

**Symptom**: `systemctl status nexusai-api` shows "failed" status

**Solution**:
```bash
# Check detailed error logs
sudo journalctl -u nexusai-api -n 100 --no-pager

# Common causes:
# 1. Port 8000 already in use
sudo lsof -i :8000
# Kill conflicting process or change port in configuration

# 2. Permission issues
sudo chown -R nexusai:nexusai /opt/nexusai
sudo chmod -R 755 /opt/nexusai

# 3. Missing environment file
ls -la /opt/nexusai/.env
# Create .env from .env.example if missing

# Restart service after fixing
sudo systemctl restart nexusai-api
```

#### Issue 5: Slow Response Times (> 10 seconds)

**Symptom**: Queries take longer than 10 seconds to respond

**Solution**:
```bash
# Check system resources
htop  # Look for CPU/RAM bottlenecks

# Check concurrent requests
curl http://localhost:8000/api/metrics | jq '.queue_depth'

# If queue depth > 20, system is overloaded
# Solutions:
# 1. Reduce MAX_CONCURRENT_INFERENCE in .env (try 3 instead of 5)
# 2. Upgrade hardware (more CPU cores, more RAM)
# 3. Implement caching (install Redis)

# Check ChromaDB performance
python scripts/benchmark_chromadb.py

# If ChromaDB is slow, rebuild indexes:
python scripts/rebuild_chromadb_indexes.py
```

#### Issue 6: ChromaDB Collection Empty

**Symptom**: Queries return "No relevant context found"

**Solution**:
```bash
# Check ChromaDB collections
python scripts/check_chromadb.py --list-collections

# If collections are empty, run VKP pull manually
python src/aws_control_plane/vkp_puller.py --force

# Or load sample curriculum data
python scripts/load_sample_curriculum.py

# Verify embeddings loaded
python scripts/check_chromadb.py --count-documents
```

#### Issue 7: VKP Pull Fails

**Symptom**: "VKP pull failed: Access Denied"

**Solution**:
```bash
# Check AWS credentials
aws sts get-caller-identity

# If credentials invalid, configure AWS CLI
aws configure

# Check S3 bucket access
aws s3 ls s3://nexusai-vkp-packages/

# Check IAM permissions
# Ensure school server role has s3:GetObject permission

# Test VKP pull with verbose logging
python src/aws_control_plane/vkp_puller.py --verbose
```

#### Issue 8: Database Connection Pool Exhausted

**Symptom**: `psycopg2.pool.PoolError: connection pool exhausted`

**Solution**:
```bash
# Increase connection pool size in .env
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40

# Restart API service
sudo systemctl restart nexusai-api

# Check for connection leaks
python scripts/check_db_connections.py

# If connections not being released, check application logs for errors
```

#### Issue 9: Disk Space Full

**Symptom**: "No space left on device"

**Solution**:
```bash
# Check disk usage
df -h

# Find large files
du -sh /opt/nexusai/* | sort -h

# Common space consumers:
# 1. Old backups - cleanup old backups
find /opt/nexusai/backups -name "*.tar.gz" -mtime +30 -delete

# 2. Large log files - rotate logs
sudo logrotate -f /etc/logrotate.d/nexusai

# 3. ChromaDB data - if too large, consider archiving old subjects
python scripts/archive_old_subjects.py --older-than 365
```

#### Issue 10: Memory Leak / High RAM Usage

**Symptom**: RAM usage continuously increases over time

**Solution**:
```bash
# Monitor memory usage
watch -n 5 'free -h'

# Check process memory
ps aux --sort=-%mem | head -10

# If nexusai-api consuming too much memory:
# 1. Restart service (temporary fix)
sudo systemctl restart nexusai-api

# 2. Reduce model context length in .env
MODEL_CONTEXT_LENGTH=2048  # Reduce from 4096

# 3. Enable memory mapping
MODEL_USE_MMAP=true

# 4. Implement automatic restart on high memory
# Add to systemd service file:
# MemoryMax=14G
# MemoryHigh=12G
```

### Getting Help

If you encounter issues not covered in this guide:

1. **Check Logs**:
   ```bash
   # Application logs
   tail -f /var/log/nexusai/app.log
   
   # System logs
   sudo journalctl -u nexusai-api -f
   ```

2. **Run Diagnostics**:
   ```bash
   python scripts/run_diagnostics.py --full
   ```

3. **Contact Support**:
   - Email: support@openclass-nexus.id
   - Documentation: https://docs.openclass-nexus.id
   - GitHub Issues: https://github.com/your-org/openclass-nexus-ai/issues

4. **Community Forum**:
   - Forum: https://forum.openclass-nexus.id
   - Discord: https://discord.gg/openclass-nexus

---

## Next Steps

After successful deployment:

1. **Load Curriculum Data**: Upload curriculum PDFs or run VKP pull to populate ChromaDB
2. **Create User Accounts**: Create teacher and student accounts
3. **Configure Subjects**: Setup subjects and grade levels in the system
4. **Test with Students**: Conduct pilot testing with a small group of students
5. **Monitor Performance**: Use health monitoring and metrics to track system performance
6. **Schedule Maintenance**: Plan regular maintenance windows for updates and backups

---

## Appendix

### A. Directory Structure

```
/opt/nexusai/
├── venv/                          # Python virtual environment
├── src/                           # Application source code
│   ├── api/                       # FastAPI server
│   ├── edge_runtime/              # LLM inference engine
│   ├── aws_control_plane/         # AWS integration
│   ├── persistence/               # Database layer
│   ├── pedagogy/                  # Pedagogical engine
│   ├── resilience/                # Backup and health monitoring
│   └── telemetry/                 # Metrics collection
├── models/                        # LLM models
│   └── llama-3.2-3b-instruct-q4_k_m.gguf
├── data/                          # Data storage
│   └── vector_db/                 # ChromaDB storage
├── config/                        # Configuration files
├── scripts/                       # Utility scripts
├── backups/                       # Backup storage
├── logs/                          # Application logs
├── .env                           # Environment configuration
├── requirements.txt               # Python dependencies
└── install.sh                     # Automated installer
```

### B. Port Reference

| Service | Port | Protocol | Access |
|---------|------|----------|--------|
| API Server | 8000 | HTTP | LAN only |
| PostgreSQL | 5432 | TCP | localhost only |
| Redis (optional) | 6379 | TCP | localhost only |
| Prometheus (optional) | 9090 | HTTP | localhost only |

### C. Resource Usage Estimates

| Component | CPU | RAM | Disk |
|-----------|-----|-----|------|
| LLM Model (idle) | 0% | 4GB | 4GB |
| LLM Model (inference) | 400-800% | 6-8GB | 4GB |
| PostgreSQL | 5-10% | 512MB | 10GB |
| ChromaDB | 5-10% | 1GB | 50-200GB |
| API Server | 5-10% | 512MB | 1GB |
| Total (idle) | 15-30% | 6GB | 65-215GB |
| Total (active) | 415-830% | 8-10GB | 65-215GB |

### D. Performance Benchmarks

**Single Query Performance**:
- RAG retrieval: 0.5-1.0 seconds
- LLM inference: 2-5 seconds
- Total response time: 3-8 seconds (target)

**Concurrent Performance**:
- 5 concurrent queries: 3-8 seconds per query
- 100 concurrent students (20 queries/min): Stable
- 300 concurrent students (60 queries/min): Acceptable degradation

**Database Performance**:
- User authentication: < 50ms
- Chat history save: < 100ms
- Mastery tracking update: < 100ms

---

**Deployment Guide Version**: 1.0.0  
**Last Updated**: February 21, 2026  
**Target System**: OpenClass Nexus AI - Hybrid Orchestrated Edge AI  
**Validated For**: Requirements 19.2
