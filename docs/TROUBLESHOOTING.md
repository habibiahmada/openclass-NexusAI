# OpenClass Nexus AI - Troubleshooting Guide

## Overview

This guide helps diagnose and resolve common issues with the OpenClass Nexus AI system. The system is a Hybrid Orchestrated Edge AI platform with 100% offline inference at schools, AWS control plane for orchestration, and privacy by architecture design.

**Target Audience**: System administrators, teachers, and technical support staff

**System Components**:
- FastAPI server (API layer)
- PostgreSQL database (persistence layer)
- ChromaDB (vector database)
- Llama 3.2 3B (LLM model)
- AWS services (S3, Lambda, DynamoDB, Bedrock)

**Hardware**: 16GB RAM, 8-core CPU, 512GB SSD

**Services**:
- `nexusai-api` - Main API server
- `nexusai-health-monitor` - Health monitoring daemon

**Log Locations**:
- Application logs: `/var/log/nexusai/app.log`
- Error logs: `/var/log/nexusai/error.log`
- Health monitor: `/var/log/nexusai/health.log`
- VKP updates: `/var/log/nexusai/vkp_pull.log`
- Telemetry: `/var/log/nexusai/telemetry.log`
- Backup logs: `/var/log/nexusai/backup.log`

---

## How to Use This Guide

1. **Identify the Problem**: Use the Quick Diagnostic Checklist to identify the issue category
2. **Find the Issue**: Navigate to the relevant section (API, Database, LLM, etc.)
3. **Follow Solutions**: Apply the recommended solutions step by step
4. **Verify Fix**: Use the verification commands to confirm the issue is resolved
5. **Prevent Recurrence**: Review prevention tips to avoid future issues

**Emergency Contact**: If critical issues persist, contact support@openclass-nexus.id

---

## Quick Diagnostic Checklist

Run this checklist to quickly identify the problem area:

```bash
# 1. Check system services
sudo systemctl status nexusai-api
sudo systemctl status nexusai-health-monitor
sudo systemctl status postgresql

# 2. Check system resources
free -h                    # RAM usage
df -h                      # Disk space
top -bn1 | head -20        # CPU usage

# 3. Check API health
curl http://localhost:8000/health

# 4. Check database connection
sudo -u postgres psql -d nexusai_db -c "SELECT 1;"

# 5. Check recent errors
tail -50 /var/log/nexusai/error.log

# 6. Check model file
ls -lh /opt/nexusai/models/*.gguf
```

**Symptom-to-Section Quick Reference**:
- System won't start → [Service Issues](#service-issues)
- Slow responses → [Performance Issues](#performance-issues)
- Database errors → [Database Issues](#database-issues)
- No responses → [LLM Inference Issues](#llm-inference-issues)
- Empty search results → [ChromaDB Issues](#chromadb-issues)
- AWS sync failures → [AWS Integration Issues](#aws-integration-issues)
- High resource usage → [Resource Management Issues](#resource-management-issues)

---

## Service Issues

### Issue 1: API Service Won't Start

**Symptoms**:
- `systemctl status nexusai-api` shows "failed" or "inactive"
- Cannot access http://localhost:8000
- Error: "Address already in use"

**Causes**:
- Port 8000 already in use by another process
- Missing or invalid configuration file
- Permission issues
- Missing dependencies

**Solutions**:

```bash
# 1. Check detailed error logs
sudo journalctl -u nexusai-api -n 100 --no-pager

# 2. Check if port 8000 is in use
sudo lsof -i :8000
# If another process is using it, kill it:
sudo kill -9 <PID>
# Or change port in .env file

# 3. Verify configuration file exists
ls -la /opt/nexusai/.env
# If missing, copy from example:
cp /opt/nexusai/.env.example /opt/nexusai/.env

# 4. Check file permissions
sudo chown -R nexusai:nexusai /opt/nexusai
sudo chmod -R 755 /opt/nexusai

# 5. Verify Python dependencies
cd /opt/nexusai
source venv/bin/activate
pip list | grep -E "fastapi|uvicorn|psycopg2"

# 6. Try starting manually to see errors
cd /opt/nexusai
source venv/bin/activate
python src/api/server.py

# 7. Restart service
sudo systemctl restart nexusai-api
sudo systemctl status nexusai-api
```

**Prevention**:
- Use systemd service management (don't run manually)
- Keep .env file backed up
- Monitor service status with health monitor

---

### Issue 2: Service Crashes Repeatedly

**Symptoms**:
- Service starts but crashes within minutes
- Repeated restart attempts in logs
- Error: "Service start request repeated too quickly"

**Causes**:
- Memory exhaustion (OOM killer)
- Unhandled exceptions in code
- Database connection failures
- Model loading failures

**Solutions**:

```bash
# 1. Check system logs for OOM killer
sudo dmesg | grep -i "killed process"
sudo journalctl -k | grep -i "out of memory"

# 2. Check available memory
free -h
# If RAM < 6GB available, system is overloaded

# 3. Check service restart limits
sudo systemctl show nexusai-api | grep Restart

# 4. Increase restart delay in service file
sudo nano /etc/systemd/system/nexusai-api.service
# Add: RestartSec=30

# 5. Check for unhandled exceptions
tail -100 /var/log/nexusai/error.log

# 6. Reduce memory usage
# Edit .env file:
MODEL_CONTEXT_LENGTH=2048  # Reduce from 4096
MAX_CONCURRENT_INFERENCE=3  # Reduce from 5

# 7. Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart nexusai-api
```

**Prevention**:
- Monitor memory usage regularly
- Set up automatic alerts for high memory usage
- Configure memory limits in systemd service file

---

### Issue 3: Health Monitor Not Running

**Symptoms**:
- `systemctl status nexusai-health-monitor` shows "inactive"
- No automatic recovery from failures
- Missing health check logs

**Causes**:
- Service not enabled at boot
- Dependency on API service failed
- Configuration errors

**Solutions**:

```bash
# 1. Check service status
sudo systemctl status nexusai-health-monitor

# 2. Check service logs
sudo journalctl -u nexusai-health-monitor -n 50

# 3. Enable and start service
sudo systemctl enable nexusai-health-monitor
sudo systemctl start nexusai-health-monitor

# 4. Verify it's running
sudo systemctl is-active nexusai-health-monitor

# 5. Check health monitor logs
tail -f /var/log/nexusai/health.log
```

**Prevention**:
- Ensure service is enabled: `sudo systemctl enable nexusai-health-monitor`
- Monitor health monitor status in weekly checks

---

## Database Issues

### Issue 4: PostgreSQL Connection Failed

**Symptoms**:
- Error: "psycopg2.OperationalError: could not connect to server"
- Error: "FATAL: database 'nexusai_db' does not exist"
- API returns 503 Service Unavailable

**Causes**:
- PostgreSQL service not running
- Database not created
- Incorrect connection credentials
- Connection pool exhausted

**Solutions**:

```bash
# 1. Check PostgreSQL status
sudo systemctl status postgresql

# 2. If not running, start it
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 3. Check if database exists
sudo -u postgres psql -l | grep nexusai

# 4. If database missing, create it
sudo -u postgres psql << EOF
CREATE DATABASE nexusai_db;
CREATE USER nexusai_user WITH ENCRYPTED PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE nexusai_db TO nexusai_user;
\q
EOF

# 5. Test connection
sudo -u postgres psql -d nexusai_db -c "SELECT 1;"

# 6. Check connection string in .env
cat /opt/nexusai/.env | grep DATABASE_URL
# Should be: postgresql://nexusai_user:password@localhost:5432/nexusai_db

# 7. Check PostgreSQL logs
sudo tail -50 /var/log/postgresql/postgresql-14-main.log

# 8. Restart API service
sudo systemctl restart nexusai-api
```

**Prevention**:
- Enable PostgreSQL auto-start: `sudo systemctl enable postgresql`
- Monitor database connection in health checks
- Keep database credentials backed up securely

---

### Issue 5: Connection Pool Exhausted

**Symptoms**:
- Error: "psycopg2.pool.PoolError: connection pool exhausted"
- Slow database queries
- Increasing response times

**Causes**:
- Too many concurrent requests
- Connection leaks (not releasing connections)
- Pool size too small

**Solutions**:

```bash
# 1. Check active connections
sudo -u postgres psql -d nexusai_db -c "SELECT count(*) FROM pg_stat_activity;"

# 2. Check connection pool settings in .env
cat /opt/nexusai/.env | grep DATABASE_POOL

# 3. Increase pool size
# Edit .env:
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40

# 4. Check for connection leaks
# Look for unclosed connections in logs
grep -i "connection" /var/log/nexusai/error.log

# 5. Kill idle connections (temporary fix)
sudo -u postgres psql -d nexusai_db << EOF
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'nexusai_db'
  AND state = 'idle'
  AND state_change < NOW() - INTERVAL '10 minutes';
EOF

# 6. Restart API service
sudo systemctl restart nexusai-api
```

**Prevention**:
- Use context managers for database connections
- Monitor connection pool metrics
- Set appropriate pool size based on load

---

### Issue 6: Database Disk Space Full

**Symptoms**:
- Error: "No space left on device"
- Cannot insert new records
- Backup failures

**Causes**:
- Chat history table too large
- Old backups not cleaned up
- PostgreSQL WAL files accumulating

**Solutions**:

```bash
# 1. Check disk usage
df -h
du -sh /opt/nexusai/* | sort -h

# 2. Check database size
sudo -u postgres psql -d nexusai_db -c "SELECT pg_size_pretty(pg_database_size('nexusai_db'));"

# 3. Check table sizes
sudo -u postgres psql -d nexusai_db << EOF
SELECT tablename, pg_size_pretty(pg_total_relation_size(tablename::regclass))
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(tablename::regclass) DESC;
EOF

# 4. Archive old chat history (older than 1 year)
sudo -u postgres psql -d nexusai_db << EOF
DELETE FROM chat_history WHERE created_at < NOW() - INTERVAL '1 year';
VACUUM FULL chat_history;
EOF

# 5. Clean up old backups
find /opt/nexusai/backups -name "*.tar.gz" -mtime +30 -delete

# 6. Clean up PostgreSQL WAL files
sudo -u postgres psql -c "CHECKPOINT;"

# 7. Verify space freed
df -h
```

**Prevention**:
- Set up automatic cleanup of old chat history
- Configure backup retention policy (28 days)
- Monitor disk usage with alerts at 80%

---

## LLM Inference Issues

### Issue 7: Model File Not Found or Corrupted

**Symptoms**:
- Error: "Model file not found"
- Error: "Failed to load model"
- Service starts but cannot process queries

**Causes**:
- Model file missing or deleted
- Incomplete download
- File corruption
- Wrong file path in configuration

**Solutions**:

```bash
# 1. Check if model file exists
ls -lh /opt/nexusai/models/*.gguf

# 2. Check model path in configuration
cat /opt/nexusai/.env | grep MODEL_PATH

# 3. Verify model file integrity
cd /opt/nexusai
source venv/bin/activate
python scripts/verify_model.py

# 4. If model missing or corrupted, re-download
python scripts/download_model.py --model llama-3.2-3b-instruct-q4_k_m

# 5. Or download manually
wget -c https://huggingface.co/TheBloke/Llama-3.2-3B-Instruct-GGUF/resolve/main/llama-3.2-3b-instruct-q4_k_m.gguf \
  -O /opt/nexusai/models/llama-3.2-3b-instruct-q4_k_m.gguf

# 6. Set correct permissions
sudo chown nexusai:nexusai /opt/nexusai/models/*.gguf
sudo chmod 644 /opt/nexusai/models/*.gguf

# 7. Restart API service
sudo systemctl restart nexusai-api
```

**Prevention**:
- Keep model file backed up
- Verify model integrity after download
- Use checksums to detect corruption

---

### Issue 8: Inference Timeout or Very Slow

**Symptoms**:
- Queries take > 30 seconds
- Timeout errors
- High CPU usage during inference

**Causes**:
- Insufficient CPU resources
- Too many concurrent inferences
- Model context length too large
- System overloaded

**Solutions**:

```bash
# 1. Check CPU usage
top -bn1 | head -20
htop  # Interactive view

# 2. Check concurrent inference count
curl http://localhost:8000/api/metrics | jq '.active_inferences'

# 3. Reduce concurrent inference limit
# Edit .env:
MAX_CONCURRENT_INFERENCE=3  # Reduce from 5

# 4. Reduce model context length
# Edit .env:
MODEL_CONTEXT_LENGTH=2048  # Reduce from 4096

# 5. Reduce max tokens per response
# Edit .env:
MODEL_MAX_TOKENS=256  # Reduce from 512

# 6. Check for other CPU-intensive processes
ps aux --sort=-%cpu | head -10

# 7. Restart API service with new settings
sudo systemctl restart nexusai-api

# 8. Test inference speed
curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "Test", "subject_id": 1}' \
  -w "\nTime: %{time_total}s\n"
```

**Prevention**:
- Monitor CPU usage and set alerts
- Tune concurrency based on hardware
- Use caching for repeated questions

---

### Issue 9: Out of Memory During Inference

**Symptoms**:
- Error: "Out of memory"
- Service crashes during query processing
- System becomes unresponsive

**Causes**:
- Model too large for available RAM
- Memory leak
- Too many concurrent inferences

**Solutions**:

```bash
# 1. Check memory usage
free -h
ps aux --sort=-%mem | head -10

# 2. Check for OOM killer events
sudo dmesg | grep -i "out of memory"

# 3. Enable memory mapping for model
# Edit .env:
MODEL_USE_MMAP=true

# 4. Reduce concurrent inferences
# Edit .env:
MAX_CONCURRENT_INFERENCE=2

# 5. Clear system cache (temporary relief)
sudo sync
sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'

# 6. Add swap space if needed (not recommended for production)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 7. Restart service
sudo systemctl restart nexusai-api

# 8. Monitor memory usage
watch -n 5 'free -h'
```

**Prevention**:
- Ensure 16GB RAM minimum
- Monitor memory usage continuously
- Set memory limits in systemd service file
- Use memory-mapped model loading

---

## ChromaDB Issues

### Issue 10: ChromaDB Connection Failed

**Symptoms**:
- Error: "Failed to connect to ChromaDB"
- Error: "Collection not found"
- Empty search results

**Causes**:
- ChromaDB not initialized
- Corrupted database files
- Permission issues
- Wrong database path

**Solutions**:

```bash
# 1. Check ChromaDB directory
ls -la /opt/nexusai/data/vector_db/

# 2. Check ChromaDB path in configuration
cat /opt/nexusai/.env | grep CHROMADB_PATH

# 3. Verify ChromaDB installation
cd /opt/nexusai
source venv/bin/activate
python -c "import chromadb; print(chromadb.__version__)"

# 4. Test ChromaDB connection
python scripts/check_chromadb.py

# 5. If corrupted, reinitialize ChromaDB
# CAUTION: This deletes all embeddings
rm -rf /opt/nexusai/data/vector_db/*
python scripts/setup_chromadb.py --init-collections

# 6. Check permissions
sudo chown -R nexusai:nexusai /opt/nexusai/data/vector_db
sudo chmod -R 755 /opt/nexusai/data/vector_db

# 7. Restart API service
sudo systemctl restart nexusai-api
```

**Prevention**:
- Include ChromaDB in backup strategy
- Monitor ChromaDB health in health checks
- Keep ChromaDB version updated

---

### Issue 11: No Search Results / Empty Collections

**Symptoms**:
- Queries return "No relevant context found"
- ChromaDB collections are empty
- Zero documents in collections

**Causes**:
- VKP updates not run
- VKP extraction failed
- Wrong collection name
- Embeddings not loaded

**Solutions**:

```bash
# 1. Check ChromaDB collections
cd /opt/nexusai
source venv/bin/activate
python scripts/check_chromadb.py --list-collections

# 2. Count documents in collections
python scripts/check_chromadb.py --count-documents

# 3. Check VKP pull logs
tail -50 /var/log/nexusai/vkp_pull.log

# 4. Run VKP pull manually
python src/aws_control_plane/vkp_puller.py --force

# 5. Or load sample curriculum data
python scripts/load_sample_curriculum.py

# 6. Verify embeddings loaded
python scripts/check_chromadb.py --verify-embeddings

# 7. Check collection name in configuration
cat /opt/nexusai/.env | grep CHROMADB_COLLECTION_NAME

# 8. Test search functionality
python scripts/test_chromadb_search.py --query "test query"
```

**Prevention**:
- Ensure VKP pull cron job is running
- Monitor collection document counts
- Verify VKP updates complete successfully

---

## AWS Integration Issues

### Issue 12: VKP Update Failed

**Symptoms**:
- Error: "AWS credentials not configured"
- Error: "S3 bucket not found"
- Error: "Access Denied"
- VKP updates not downloading

**Causes**:
- Missing AWS credentials
- Incorrect IAM permissions
- S3 bucket doesn't exist
- Network connectivity issues

**Solutions**:

```bash
# 1. Check AWS credentials
aws sts get-caller-identity

# 2. If credentials missing, configure AWS CLI
aws configure
# Enter: Access Key ID, Secret Access Key, Region (ap-southeast-1)

# 3. Test S3 bucket access
aws s3 ls s3://nexusai-vkp-packages/

# 4. Check IAM permissions
aws iam get-user

# 5. Verify bucket exists
aws s3api head-bucket --bucket nexusai-vkp-packages

# 6. Check network connectivity
ping -c 4 s3.ap-southeast-1.amazonaws.com

# 7. Run VKP pull with verbose logging
cd /opt/nexusai
source venv/bin/activate
python src/aws_control_plane/vkp_puller.py --verbose

# 8. Check VKP pull cron job
crontab -l | grep vkp_puller

# 9. Test manual VKP download
aws s3 cp s3://nexusai-vkp-packages/matematika/kelas_10/v1.0.0.vkp /tmp/test.vkp
```

**Prevention**:
- Keep AWS credentials backed up securely
- Monitor VKP pull logs regularly
- Set up alerts for VKP update failures
- Test AWS connectivity periodically

---

### Issue 13: Telemetry Upload Failed

**Symptoms**:
- Error: "Failed to upload telemetry"
- Error: "DynamoDB table not found"
- Telemetry queue growing

**Causes**:
- Missing AWS credentials
- DynamoDB table doesn't exist
- Network connectivity issues
- IAM permission issues

**Solutions**:

```bash
# 1. Check telemetry logs
tail -50 /var/log/nexusai/telemetry.log

# 2. Check AWS credentials
aws sts get-caller-identity

# 3. Verify DynamoDB table exists
aws dynamodb describe-table --table-name nexusai-metrics

# 4. Check telemetry queue
ls -lh /opt/nexusai/data/telemetry_queue.json

# 5. Test DynamoDB write
aws dynamodb put-item \
  --table-name nexusai-metrics \
  --item '{"school_id": {"S": "test"}, "timestamp": {"N": "1234567890"}}'

# 6. Run telemetry upload manually
cd /opt/nexusai
source venv/bin/activate
python src/telemetry/telemetry_uploader.py --verbose

# 7. If telemetry not critical, disable temporarily
# Edit .env:
TELEMETRY_ENABLED=false

# 8. Restart API service
sudo systemctl restart nexusai-api
```

**Prevention**:
- Telemetry is optional - system works without it
- Monitor telemetry queue size
- Set up retry mechanism for failed uploads

---

## Performance Issues

### Issue 14: Slow Response Times (> 10 seconds)

**Symptoms**:
- Queries take longer than 10 seconds
- Users complain about slow system
- High queue depth

**Causes**:
- System overloaded (too many concurrent users)
- Insufficient CPU/RAM
- ChromaDB index slow
- No caching enabled

**Solutions**:

```bash
# 1. Check system resources
top -bn1 | head -20
free -h
df -h

# 2. Check queue depth
curl http://localhost:8000/api/metrics | jq '.queue_depth'

# 3. Check concurrent requests
curl http://localhost:8000/api/metrics | jq '.active_inferences'

# 4. Benchmark ChromaDB search
cd /opt/nexusai
source venv/bin/activate
python scripts/benchmark_chromadb.py

# 5. If ChromaDB slow, rebuild indexes
python scripts/rebuild_chromadb_indexes.py

# 6. Enable Redis caching
sudo apt install redis-server
sudo systemctl start redis
sudo systemctl enable redis

# Edit .env:
REDIS_URL=redis://localhost:6379/0
CACHE_TTL_SECONDS=86400

# 7. Reduce concurrent inference limit
# Edit .env:
MAX_CONCURRENT_INFERENCE=3

# 8. Optimize model settings
# Edit .env:
MODEL_CONTEXT_LENGTH=2048
MODEL_MAX_TOKENS=256
MODEL_N_THREADS=6

# 9. Restart API service
sudo systemctl restart nexusai-api

# 10. Monitor response times
tail -f /var/log/nexusai/app.log | grep "response_time"
```

**Prevention**:
- Monitor response times continuously
- Set up alerts for response time > 8 seconds
- Use caching for repeated questions
- Scale hardware if consistently overloaded

---

### Issue 15: High CPU Usage

**Symptoms**:
- CPU usage consistently > 90%
- System becomes sluggish
- Inference very slow

**Causes**:
- Too many concurrent inferences
- Model using too many threads
- Other processes consuming CPU

**Solutions**:

```bash
# 1. Check CPU usage by process
top -bn1 | head -20
ps aux --sort=-%cpu | head -10

# 2. Check model thread count
cat /opt/nexusai/.env | grep MODEL_N_THREADS

# 3. Reduce model threads
# Edit .env:
MODEL_N_THREADS=4  # Reduce from 8

# 4. Reduce concurrent inferences
# Edit .env:
MAX_CONCURRENT_INFERENCE=2

# 5. Check for runaway processes
ps aux | grep python

# 6. Kill unnecessary processes
sudo kill -9 <PID>

# 7. Restart API service
sudo systemctl restart nexusai-api

# 8. Monitor CPU usage
watch -n 2 'top -bn1 | head -20'
```

**Prevention**:
- Set appropriate thread count for CPU cores
- Monitor CPU usage with alerts
- Limit concurrent inferences based on capacity

---

### Issue 16: High Memory Usage / Memory Leak

**Symptoms**:
- RAM usage continuously increases
- System becomes slow over time
- Eventually crashes with OOM

**Causes**:
- Memory leak in application code
- Model not using memory mapping
- Too many cached objects
- Database connection leaks

**Solutions**:

```bash
# 1. Check memory usage
free -h
ps aux --sort=-%mem | head -10

# 2. Monitor memory over time
watch -n 5 'free -h'

# 3. Enable memory mapping for model
# Edit .env:
MODEL_USE_MMAP=true

# 4. Reduce cache size
# Edit .env:
CACHE_MAX_SIZE=500  # Reduce from 1000

# 5. Check for connection leaks
sudo -u postgres psql -d nexusai_db -c "SELECT count(*) FROM pg_stat_activity;"

# 6. Restart service (temporary fix)
sudo systemctl restart nexusai-api

# 7. Set memory limits in systemd
sudo nano /etc/systemd/system/nexusai-api.service
# Add:
# MemoryMax=14G
# MemoryHigh=12G

sudo systemctl daemon-reload
sudo systemctl restart nexusai-api

# 8. Enable automatic restart on high memory
# Add to systemd service:
# Restart=on-failure
# RestartSec=30
```

**Prevention**:
- Monitor memory usage trends
- Set memory limits in systemd
- Use memory-mapped model loading
- Implement automatic restart on high memory

---

## Resource Management Issues

### Issue 17: Disk Space Full

**Symptoms**:
- Error: "No space left on device"
- Cannot save chat history
- Backup failures

**Causes**:
- Large chat history table
- Old backups not cleaned up
- Large log files
- ChromaDB data too large

**Solutions**:

```bash
# 1. Check disk usage
df -h
du -sh /opt/nexusai/* | sort -h

# 2. Find large files
find /opt/nexusai -type f -size +100M -exec ls -lh {} \;

# 3. Clean up old backups (older than 30 days)
find /opt/nexusai/backups -name "*.tar.gz" -mtime +30 -delete

# 4. Rotate and compress logs
sudo logrotate -f /etc/logrotate.d/nexusai

# 5. Archive old chat history
sudo -u postgres psql -d nexusai_db << EOF
DELETE FROM chat_history WHERE created_at < NOW() - INTERVAL '1 year';
VACUUM FULL chat_history;
EOF

# 6. Clean up temporary files
rm -rf /opt/nexusai/tmp/*
rm -rf /tmp/nexusai_*

# 7. Check ChromaDB size
du -sh /opt/nexusai/data/vector_db/

# 8. If ChromaDB too large, archive old subjects
python scripts/archive_old_subjects.py --older-than 365

# 9. Verify space freed
df -h
```

**Prevention**:
- Set up automatic cleanup cron jobs
- Monitor disk usage with alerts at 80%
- Configure log rotation
- Implement backup retention policy (28 days)

---

### Issue 18: Network Connectivity Issues

**Symptoms**:
- Cannot access API from student devices
- VKP updates fail
- Telemetry upload fails

**Causes**:
- Firewall blocking connections
- Network configuration issues
- Server not on correct network
- DNS issues

**Solutions**:

```bash
# 1. Check server IP address
ip addr show

# 2. Check if API is listening
sudo netstat -tlnp | grep 8000

# 3. Test local access
curl http://localhost:8000/health

# 4. Test from another device on LAN
curl http://<server-ip>:8000/health

# 5. Check firewall rules
sudo ufw status verbose

# 6. Allow API access from LAN
sudo ufw allow from 192.168.1.0/24 to any port 8000 proto tcp

# 7. Check internet connectivity
ping -c 4 8.8.8.8
ping -c 4 google.com

# 8. Test AWS connectivity
ping -c 4 s3.ap-southeast-1.amazonaws.com

# 9. Check DNS resolution
nslookup google.com

# 10. Restart network service
sudo systemctl restart networking
```

**Prevention**:
- Document network configuration
- Keep firewall rules documented
- Test connectivity regularly
- Set up monitoring for network issues

---

## Error Message Reference

### Common Error Messages and Solutions

**"Address already in use"**
- **Cause**: Port 8000 is already in use
- **Solution**: Kill the process using port 8000 or change the port
- **Command**: `sudo lsof -i :8000` then `sudo kill -9 <PID>`

**"psycopg2.OperationalError: could not connect to server"**
- **Cause**: PostgreSQL not running or wrong connection string
- **Solution**: Start PostgreSQL and verify connection string
- **Command**: `sudo systemctl start postgresql`

**"Model file not found"**
- **Cause**: LLM model file missing or wrong path
- **Solution**: Download model or fix MODEL_PATH in .env
- **Command**: `python scripts/download_model.py`

**"Out of memory"**
- **Cause**: Insufficient RAM or memory leak
- **Solution**: Enable memory mapping, reduce concurrent inferences
- **Command**: Set `MODEL_USE_MMAP=true` in .env

**"Connection pool exhausted"**
- **Cause**: Too many database connections
- **Solution**: Increase pool size or fix connection leaks
- **Command**: Increase `DATABASE_POOL_SIZE` in .env

**"No space left on device"**
- **Cause**: Disk full
- **Solution**: Clean up old backups, logs, and chat history
- **Command**: `find /opt/nexusai/backups -mtime +30 -delete`

**"AWS credentials not configured"**
- **Cause**: Missing AWS credentials
- **Solution**: Configure AWS CLI
- **Command**: `aws configure`

**"S3 bucket not found"**
- **Cause**: Bucket doesn't exist or wrong region
- **Solution**: Verify bucket name and region
- **Command**: `aws s3 ls s3://nexusai-vkp-packages/`

**"Failed to connect to ChromaDB"**
- **Cause**: ChromaDB not initialized or corrupted
- **Solution**: Reinitialize ChromaDB
- **Command**: `python scripts/setup_chromadb.py --init-collections`

**"No relevant context found"**
- **Cause**: ChromaDB collections empty
- **Solution**: Run VKP pull or load sample data
- **Command**: `python src/aws_control_plane/vkp_puller.py --force`

**"Service start request repeated too quickly"**
- **Cause**: Service crashing repeatedly
- **Solution**: Check logs for root cause, increase RestartSec
- **Command**: `sudo journalctl -u nexusai-api -n 100`

---

## Debugging Tools and Commands

### System Health Check

```bash
# Comprehensive health check
cd /opt/nexusai
source venv/bin/activate
python scripts/check_system_health.py
```

### Service Status

```bash
# Check all services
sudo systemctl status nexusai-api
sudo systemctl status nexusai-health-monitor
sudo systemctl status postgresql
sudo systemctl status redis  # If using Redis
```

### Log Analysis

```bash
# View recent errors
tail -50 /var/log/nexusai/error.log

# Follow application logs
tail -f /var/log/nexusai/app.log

# Search for specific errors
grep -i "error" /var/log/nexusai/app.log | tail -20

# View systemd service logs
sudo journalctl -u nexusai-api -n 100 --no-pager
sudo journalctl -u nexusai-api -f  # Follow logs
```

### Resource Monitoring

```bash
# CPU and memory usage
top -bn1 | head -20
htop  # Interactive

# Memory details
free -h
cat /proc/meminfo

# Disk usage
df -h
du -sh /opt/nexusai/* | sort -h

# Network connections
sudo netstat -tlnp
sudo ss -tlnp

# Process list
ps aux --sort=-%cpu | head -10
ps aux --sort=-%mem | head -10
```

### Database Diagnostics

```bash
# Connect to database
sudo -u postgres psql -d nexusai_db

# Check database size
sudo -u postgres psql -d nexusai_db -c "SELECT pg_size_pretty(pg_database_size('nexusai_db'));"

# Check table sizes
sudo -u postgres psql -d nexusai_db << EOF
SELECT tablename, pg_size_pretty(pg_total_relation_size(tablename::regclass))
FROM pg_tables WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(tablename::regclass) DESC;
EOF

# Check active connections
sudo -u postgres psql -d nexusai_db -c "SELECT count(*) FROM pg_stat_activity;"

# Check slow queries
sudo -u postgres psql -d nexusai_db -c "SELECT query, state, wait_event FROM pg_stat_activity WHERE state != 'idle';"
```

### API Testing

```bash
# Health check
curl http://localhost:8000/health

# Get metrics
curl http://localhost:8000/api/metrics

# Test authentication
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your_password"}'

# Test query (with token)
TOKEN="your_token_here"
curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "Test question", "subject_id": 1}' \
  -w "\nTime: %{time_total}s\n"
```

### ChromaDB Diagnostics

```bash
cd /opt/nexusai
source venv/bin/activate

# List collections
python scripts/check_chromadb.py --list-collections

# Count documents
python scripts/check_chromadb.py --count-documents

# Test search
python scripts/test_chromadb_search.py --query "test"

# Benchmark performance
python scripts/benchmark_chromadb.py
```

### AWS Diagnostics

```bash
# Check AWS credentials
aws sts get-caller-identity

# List S3 buckets
aws s3 ls

# Check VKP bucket
aws s3 ls s3://nexusai-vkp-packages/ --recursive

# Test DynamoDB access
aws dynamodb describe-table --table-name nexusai-metrics

# Check Lambda functions
aws lambda list-functions

# View CloudWatch logs
aws logs tail /aws/lambda/nexusai-curriculum-processor --follow
```

### Performance Benchmarking

```bash
cd /opt/nexusai
source venv/bin/activate

# Benchmark inference speed
python scripts/benchmark_inference.py

# Benchmark database queries
python scripts/benchmark_database.py

# Benchmark ChromaDB search
python scripts/benchmark_chromadb.py

# Load test (simulate concurrent users)
python scripts/load_test.py --users 50 --duration 60
```

---

## When to Seek Help

Contact technical support if:

1. **Critical System Failure**
   - System completely unresponsive
   - Data corruption detected
   - Cannot restore from backup

2. **Persistent Issues**
   - Problem persists after following all troubleshooting steps
   - Issue recurs frequently despite fixes
   - Root cause unclear

3. **Security Concerns**
   - Suspected security breach
   - Unauthorized access detected
   - Data privacy concerns

4. **Performance Degradation**
   - System consistently fails to meet performance targets
   - Hardware upgrade needed but unsure of specifications
   - Optimization advice needed

5. **Complex Configuration**
   - AWS integration issues
   - Custom deployment scenarios
   - Multi-school federation setup

### Support Channels

**Email Support**: support@openclass-nexus.id
- Response time: 24-48 hours
- Include: System logs, error messages, steps taken

**Documentation**: https://docs.openclass-nexus.id
- Comprehensive guides
- API documentation
- Architecture details

**Community Forum**: https://forum.openclass-nexus.id
- Community support
- Share experiences
- Feature requests

**Emergency Hotline**: +62-XXX-XXXX-XXXX
- Critical issues only
- Available 24/7
- Response time: 2-4 hours

### Information to Provide

When contacting support, include:

1. **System Information**
   ```bash
   uname -a
   cat /etc/os-release
   free -h
   df -h
   ```

2. **Service Status**
   ```bash
   sudo systemctl status nexusai-api
   sudo systemctl status postgresql
   ```

3. **Recent Logs**
   ```bash
   tail -100 /var/log/nexusai/error.log
   sudo journalctl -u nexusai-api -n 100
   ```

4. **Configuration** (sanitize sensitive data)
   ```bash
   cat /opt/nexusai/.env | grep -v PASSWORD | grep -v SECRET
   ```

5. **Error Messages**
   - Exact error text
   - When it occurred
   - What action triggered it

6. **Steps Taken**
   - Troubleshooting steps already attempted
   - Results of each step
   - Any temporary workarounds applied

---

## Preventive Maintenance

### Daily Tasks

```bash
# Check service status
sudo systemctl status nexusai-api
sudo systemctl status nexusai-health-monitor

# Check disk space
df -h

# Check recent errors
tail -20 /var/log/nexusai/error.log
```

### Weekly Tasks

```bash
# Review health monitor logs
tail -100 /var/log/nexusai/health.log

# Check database size
sudo -u postgres psql -d nexusai_db -c "SELECT pg_size_pretty(pg_database_size('nexusai_db'));"

# Verify backups completed
ls -lh /opt/nexusai/backups/ | tail -10

# Check VKP updates
tail -50 /var/log/nexusai/vkp_pull.log

# Review system resources
free -h
df -h
top -bn1 | head -20
```

### Monthly Tasks

```bash
# Run full system health check
python scripts/check_system_health.py --full

# Vacuum database
sudo -u postgres psql -d nexusai_db -c "VACUUM ANALYZE;"

# Reindex database
sudo -u postgres psql -d nexusai_db -c "REINDEX DATABASE nexusai_db;"

# Clean up old chat history (> 1 year)
sudo -u postgres psql -d nexusai_db -c "DELETE FROM chat_history WHERE created_at < NOW() - INTERVAL '1 year';"

# Update system packages
sudo apt update && sudo apt upgrade -y

# Review and rotate logs
sudo logrotate -f /etc/logrotate.d/nexusai
```

### Quarterly Tasks

```bash
# Test backup restoration
# (In test environment, not production!)
python scripts/test_backup_restore.py

# Review and update documentation
# Update any changed configurations

# Performance audit
python scripts/performance_audit.py

# Security audit
python scripts/security_audit.py

# Capacity planning review
# Analyze growth trends and plan upgrades
```

---

## Appendix: Configuration Reference

### Environment Variables (.env)

**Database Configuration**:
```bash
DATABASE_URL=postgresql://nexusai_user:password@localhost:5432/nexusai_db
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
```

**Model Configuration**:
```bash
MODEL_PATH=/opt/nexusai/models/llama-3.2-3b-instruct-q4_k_m.gguf
MODEL_CONTEXT_LENGTH=4096
MODEL_N_THREADS=8
MODEL_MAX_TOKENS=512
MODEL_USE_MMAP=true
```

**Concurrency Configuration**:
```bash
MAX_CONCURRENT_INFERENCE=5
MAX_QUEUE_SIZE=1000
```

**ChromaDB Configuration**:
```bash
CHROMADB_PATH=/opt/nexusai/data/vector_db
CHROMADB_COLLECTION_NAME=curriculum_embeddings
```

**AWS Configuration**:
```bash
AWS_REGION=ap-southeast-1
AWS_S3_VKP_BUCKET=nexusai-vkp-packages
AWS_DYNAMODB_METRICS_TABLE=nexusai-metrics
```

**Caching Configuration**:
```bash
REDIS_URL=redis://localhost:6379/0
CACHE_TTL_SECONDS=86400
CACHE_FALLBACK_TO_LRU=true
```

**Logging Configuration**:
```bash
LOG_LEVEL=INFO
LOG_FILE=/var/log/nexusai/app.log
```

---

## Document Information

**Version**: 1.0.0  
**Last Updated**: February 21, 2026  
**Maintained By**: OpenClass Nexus AI Development Team  
**Validates Requirement**: 19.6

**Changelog**:
- v1.0.0 (2026-02-21): Initial troubleshooting guide created

---

**End of Troubleshooting Guide**
