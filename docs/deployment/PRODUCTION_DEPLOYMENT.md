# OpenClass Nexus AI - Production Deployment Guide

## Overview

This guide covers deploying OpenClass Nexus AI in production environments, including server setup, performance optimization, and monitoring.

## Deployment Options

### 1. Standalone Desktop Application

**Use Case**: Individual users, offline environments
**Requirements**: 4GB RAM, 10GB storage

```bash
# Create standalone package
python scripts/deployment/create_standalone.py

# Generated package structure:
openclass-nexus-standalone/
├── openclass-nexus.exe        # Main executable
├── models/                    # Embedded AI models
├── data/                      # Knowledge base
├── config/                    # Configuration files
└── README.txt                 # User instructions
```

### 2. Server Deployment

**Use Case**: Multiple users, classroom environments
**Requirements**: 8GB RAM, 50GB storage, Linux server

#### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt
RUN python scripts/setup_model.py --headless

EXPOSE 8000
CMD ["python", "src/api/server.py"]
```

```bash
# Build and run
docker build -t openclass-nexus .
docker run -p 8000:8000 -v ./data:/app/data openclass-nexus
```

#### Kubernetes Deployment

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: openclass-nexus
spec:
  replicas: 3
  selector:
    matchLabels:
      app: openclass-nexus
  template:
    metadata:
      labels:
        app: openclass-nexus
    spec:
      containers:
      - name: openclass-nexus
        image: openclass-nexus:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
          limits:
            memory: "8Gi"
            cpu: "4"
        volumeMounts:
        - name: model-storage
          mountPath: /app/models
        - name: data-storage
          mountPath: /app/data
      volumes:
      - name: model-storage
        persistentVolumeClaim:
          claimName: model-pvc
      - name: data-storage
        persistentVolumeClaim:
          claimName: data-pvc
```

### 3. Educational Institution Setup

**Use Case**: Schools, universities, training centers
**Requirements**: Dedicated server, network infrastructure

#### Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │───▶│  API Gateway    │───▶│  AI Inference   │
│   (nginx/HAProxy│    │  (FastAPI)      │    │  (Llama-3.2-3B) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   User Auth     │    │   ChromaDB      │
                       │   (JWT/OAuth)   │    │  (Vector Store) │
                       └─────────────────┘    └─────────────────┘
```

## Server Configuration

### 1. System Requirements

#### Minimum Production Server
```bash
# Hardware
CPU: 4 cores (Intel i5 or AMD Ryzen 5)
RAM: 8GB
Storage: 100GB SSD
Network: 100Mbps

# Software
OS: Ubuntu 20.04 LTS or CentOS 8
Python: 3.11+
Docker: 20.10+
```

#### Recommended Production Server
```bash
# Hardware
CPU: 8 cores (Intel i7 or AMD Ryzen 7)
RAM: 16GB
Storage: 500GB NVMe SSD
Network: 1Gbps

# Software
OS: Ubuntu 22.04 LTS
Python: 3.11
Docker: 24.0+
Kubernetes: 1.28+
```

### 2. Environment Setup

```bash
# System preparation
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.11 python3.11-venv python3-pip
sudo apt install -y docker.io docker-compose
sudo apt install -y nginx certbot

# Create application user
sudo useradd -m -s /bin/bash openclass
sudo usermod -aG docker openclass

# Setup application directory
sudo mkdir -p /opt/openclass-nexus
sudo chown openclass:openclass /opt/openclass-nexus
```

### 3. Application Deployment

```bash
# Switch to application user
sudo su - openclass

# Clone and setup
cd /opt/openclass-nexus
git clone https://github.com/your-org/openclass-nexus.git .
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with production settings

# Setup models and database
python scripts/setup_model.py --production
python scripts/setup_knowledge_base.py --production
```

### 4. Service Configuration

```ini
# /etc/systemd/system/openclass-nexus.service
[Unit]
Description=OpenClass Nexus AI Service
After=network.target

[Service]
Type=simple
User=openclass
Group=openclass
WorkingDirectory=/opt/openclass-nexus
Environment=PATH=/opt/openclass-nexus/venv/bin
ExecStart=/opt/openclass-nexus/venv/bin/python src/api/server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable openclass-nexus
sudo systemctl start openclass-nexus
sudo systemctl status openclass-nexus
```

## Performance Optimization

### 1. Model Optimization

```python
# config/production_config.py
MODEL_CONFIG = {
    "model_name": "llama-3.2-3b-instruct",
    "context_length": 4096,
    "n_threads": 8,          # Match CPU cores
    "n_gpu_layers": 0,       # CPU-only inference
    "rope_freq_base": 10000,
    "rope_freq_scale": 1.0,
    "batch_size": 512,
    "memory_map": True,      # Enable memory mapping
    "use_mlock": True,       # Lock model in memory
}

INFERENCE_CONFIG = {
    "max_tokens": 512,
    "temperature": 0.7,
    "top_p": 0.9,
    "top_k": 40,
    "repeat_penalty": 1.1,
    "streaming": True,
}
```

### 2. Database Optimization

```python
# ChromaDB optimization
CHROMA_CONFIG = {
    "persist_directory": "/opt/openclass-nexus/data/vector_db",
    "collection_metadata": {
        "hnsw:space": "cosine",
        "hnsw:construction_ef": 200,
        "hnsw:M": 16,
        "hnsw:search_ef": 100,
    },
    "batch_size": 1000,
    "max_batch_size": 5000,
}
```

### 3. Caching Strategy

```python
# Redis caching for frequent queries
CACHE_CONFIG = {
    "redis_url": "redis://localhost:6379/0",
    "cache_ttl": 3600,       # 1 hour
    "max_cache_size": "1GB",
    "cache_patterns": [
        "frequent_questions",
        "curriculum_content",
        "model_responses"
    ]
}
```

### 4. Load Balancing

```nginx
# /etc/nginx/sites-available/openclass-nexus
upstream openclass_backend {
    server 127.0.0.1:8000 weight=1 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:8001 weight=1 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:8002 weight=1 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://openclass_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeout settings for AI inference
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Static files
    location /static/ {
        alias /opt/openclass-nexus/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

## Monitoring and Logging

### 1. Application Monitoring

```python
# src/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Metrics collection
QUERY_COUNTER = Counter('openclass_queries_total', 'Total queries processed')
RESPONSE_TIME = Histogram('openclass_response_time_seconds', 'Response time')
MEMORY_USAGE = Gauge('openclass_memory_usage_bytes', 'Memory usage')
MODEL_LOAD_TIME = Histogram('openclass_model_load_seconds', 'Model load time')

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "model_loaded": model_manager.is_loaded(),
        "database_ready": db_manager.is_ready(),
        "memory_usage_mb": get_memory_usage(),
        "uptime_seconds": get_uptime()
    }
```

### 2. Logging Configuration

```python
# config/logging.py
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "json": {
            "format": '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "detailed"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "/var/log/openclass-nexus/app.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "formatter": "json"
        }
    },
    "loggers": {
        "openclass": {
            "level": "INFO",
            "handlers": ["console", "file"],
            "propagate": False
        }
    }
}
```

### 3. Prometheus Monitoring

```yaml
# docker-compose.monitoring.yml
version: '3.8'
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-storage:/var/lib/grafana
      
volumes:
  grafana-storage:
```

## Security Configuration

### 1. SSL/TLS Setup

```bash
# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 2. API Security

```python
# src/api/security.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=["HS256"]
        )
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
```

### 3. Rate Limiting

```python
# Rate limiting configuration
RATE_LIMITS = {
    "queries_per_minute": 60,
    "queries_per_hour": 1000,
    "concurrent_queries": 5,
    "max_query_length": 1000,
}
```

## Backup and Recovery

### 1. Database Backup

```bash
#!/bin/bash
# scripts/backup_database.sh

BACKUP_DIR="/opt/backups/openclass-nexus"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup ChromaDB
tar -czf $BACKUP_DIR/chromadb_$DATE.tar.gz data/vector_db/

# Backup configuration
tar -czf $BACKUP_DIR/config_$DATE.tar.gz config/

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

### 2. Model Backup

```bash
#!/bin/bash
# scripts/backup_models.sh

MODEL_DIR="/opt/openclass-nexus/models"
BACKUP_DIR="/opt/backups/openclass-nexus/models"
DATE=$(date +%Y%m%d_%H%M%S)

# Sync models to backup location
rsync -av --delete $MODEL_DIR/ $BACKUP_DIR/current/

# Create versioned backup
cp -r $BACKUP_DIR/current $BACKUP_DIR/backup_$DATE
```

### 3. Disaster Recovery

```bash
#!/bin/bash
# scripts/restore_system.sh

BACKUP_DIR="/opt/backups/openclass-nexus"
RESTORE_DATE=$1

if [ -z "$RESTORE_DATE" ]; then
    echo "Usage: $0 <backup_date>"
    exit 1
fi

# Stop services
sudo systemctl stop openclass-nexus

# Restore database
tar -xzf $BACKUP_DIR/chromadb_$RESTORE_DATE.tar.gz -C /opt/openclass-nexus/

# Restore configuration
tar -xzf $BACKUP_DIR/config_$RESTORE_DATE.tar.gz -C /opt/openclass-nexus/

# Restart services
sudo systemctl start openclass-nexus
```

## Maintenance

### 1. Regular Updates

```bash
#!/bin/bash
# scripts/update_system.sh

# Pull latest code
git pull origin main

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Run database migrations
python scripts/migrate_database.py

# Restart services
sudo systemctl restart openclass-nexus
```

### 2. Performance Tuning

```bash
# Monitor system performance
htop
iotop
nvidia-smi  # If using GPU

# Check application metrics
curl http://localhost:8000/metrics
curl http://localhost:8000/health
```

### 3. Log Rotation

```bash
# /etc/logrotate.d/openclass-nexus
/var/log/openclass-nexus/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 openclass openclass
    postrotate
        systemctl reload openclass-nexus
    endscript
}
```

## Troubleshooting

### Common Issues

1. **High Memory Usage**
   - Reduce model context length
   - Enable memory mapping
   - Implement query queuing

2. **Slow Response Times**
   - Optimize database queries
   - Implement caching
   - Scale horizontally

3. **Model Loading Failures**
   - Check disk space
   - Verify model integrity
   - Review memory limits

### Support Contacts

- **Technical Support**: tech-support@openclass.id
- **Emergency**: +62-xxx-xxx-xxxx
- **Documentation**: https://docs.openclass.id

---

**Deployment Guide Version**: 3.0.0  
**Last Updated**: January 26, 2026  
**Environment**: Production