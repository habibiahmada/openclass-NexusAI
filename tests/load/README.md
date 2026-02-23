# Load Testing Suite

This directory contains the load testing suite for OpenClass Nexus AI, designed to validate system performance under concurrent user load.

## Requirements Tested

- **18.1**: Simulate 100 concurrent users with stable performance
- **18.2**: Simulate 300 concurrent users with acceptable degradation
- **18.3**: Maintain 3-8 second response time for 90th percentile
- **18.4**: Measure error rate and verify < 1% errors
- **18.5**: Measure queue depth and verify requests are processed
- **18.6**: Generate performance report with latency distribution

## Prerequisites

1. **Install Locust**:
   ```bash
   pip install locust
   ```

2. **Ensure Server is Running**:
   ```bash
   python api_server.py
   ```

3. **Create Test Users** (if not already created):
   ```bash
   python scripts/database/create_test_users.py
   ```

## Running Load Tests

### Test 1: 100 Concurrent Users

This test simulates 100 students using the system simultaneously, which represents comfortable utilization (~16.7%).

```bash
# Command line mode (headless)
locust -f tests/load/locustfile.py \
    --host=http://localhost:8000 \
    --users=100 \
    --spawn-rate=10 \
    --run-time=5m \
    --headless

# Web UI mode (interactive)
locust -f tests/load/locustfile.py \
    --host=http://localhost:8000
# Then open http://localhost:8089 and configure:
# - Number of users: 100
# - Spawn rate: 10 users/second
# - Run time: 5 minutes
```

**Expected Results**:
- P90 latency: 3-8 seconds
- Error rate: < 1%
- Stable performance throughout test
- Queue depth: minimal (< 10)

### Test 2: 300 Concurrent Users

This test simulates 300 students using the system simultaneously, which represents acceptable utilization (~50%).

```bash
# Command line mode (headless)
locust -f tests/load/locustfile.py \
    --host=http://localhost:8000 \
    --users=300 \
    --spawn-rate=20 \
    --run-time=5m \
    --headless

# Web UI mode (interactive)
locust -f tests/load/locustfile.py \
    --host=http://localhost:8000
# Then open http://localhost:8089 and configure:
# - Number of users: 300
# - Spawn rate: 20 users/second
# - Run time: 5 minutes
```

**Expected Results**:
- P90 latency: 3-8 seconds (acceptable degradation)
- Error rate: < 1%
- Queue depth: moderate (10-50)
- Some 503 responses (queue full) are acceptable

## Understanding the Results

### Locust Web UI

When running in web UI mode, you'll see:

1. **Statistics Tab**: Real-time request statistics
   - Request count
   - Failure rate
   - Response times (min, max, average, median)
   - Requests per second

2. **Charts Tab**: Visual graphs
   - Total requests per second
   - Response times over time
   - Number of users over time

3. **Failures Tab**: Error details
   - Failed requests with error messages
   - Useful for debugging issues

4. **Download Data**: Export results as CSV

### Performance Report

After each test, a JSON report is generated in `tests/load/reports/` with:

```json
{
  "test_summary": {
    "start_time": "2026-02-15T10:30:00",
    "end_time": "2026-02-15T10:35:00",
    "total_requests": 1250,
    "successful_requests": 1230,
    "failed_requests": 15,
    "queue_full_responses": 5
  },
  "latency_distribution": {
    "average_ms": 4500,
    "p50_ms": 4200,
    "p90_ms": 6200,
    "p99_ms": 7800,
    "min_ms": 2100,
    "max_ms": 9500
  },
  "error_metrics": {
    "error_count": 15,
    "error_rate_percent": 0.8,
    "target_error_rate": "< 1%",
    "meets_requirement": true
  },
  "performance_validation": {
    "p90_latency_ms": 6200,
    "target_range_ms": "3000-8000",
    "meets_requirement": true
  },
  "queue_statistics": {
    "max_queue_depth": 45,
    "max_active": 5
  }
}
```

## Interpreting Results

### ✅ PASS Criteria

- **P90 Latency**: Between 3000-8000ms (3-8 seconds)
- **Error Rate**: Less than 1%
- **Queue Processing**: Requests are processed (not stuck)
- **System Stability**: No crashes or service failures

### ⚠️ WARNING Signs

- P90 latency approaching 8000ms (near upper limit)
- Error rate between 0.5-1% (close to threshold)
- Queue depth consistently > 50 (potential bottleneck)
- Increasing latency over time (memory leak?)

### ❌ FAIL Criteria

- P90 latency > 8000ms (exceeds target)
- Error rate > 1% (too many failures)
- System crashes or becomes unresponsive
- Database connection failures

## Troubleshooting

### High Latency

If P90 latency exceeds 8 seconds:

1. **Check System Resources**:
   ```bash
   # CPU usage
   top
   
   # Memory usage
   free -h
   
   # Disk I/O
   iostat -x 1
   ```

2. **Check Database Performance**:
   ```bash
   # PostgreSQL connections
   psql -U nexusai -d nexusai_school -c "SELECT count(*) FROM pg_stat_activity;"
   
   # Slow queries
   psql -U nexusai -d nexusai_school -c "SELECT query, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"
   ```

3. **Check ChromaDB**:
   - Verify vector database is responding
   - Check collection size and query performance

4. **Check LLM Inference**:
   - Verify model is loaded correctly
   - Check inference time for single query

### High Error Rate

If error rate exceeds 1%:

1. **Check Logs**:
   ```bash
   tail -f logs/api_server.log
   ```

2. **Check Database Connections**:
   - Connection pool exhaustion?
   - Database deadlocks?

3. **Check Concurrency Manager**:
   - Queue overflow?
   - Thread pool issues?

### Queue Full (503 Errors)

Some 503 errors are acceptable under high load (300 users), but if excessive:

1. **Increase Concurrency Limit** (if resources allow):
   - Edit `config/app_config.py`
   - Increase `max_concurrent_threads` from 5 to 7-10
   - Monitor system resources

2. **Optimize Response Time**:
   - Enable Redis caching
   - Optimize database queries
   - Reduce LLM max_tokens if appropriate

## Advanced Testing

### Stress Testing

Test system limits by gradually increasing load:

```bash
locust -f tests/load/locustfile.py \
    --host=http://localhost:8000 \
    --users=500 \
    --spawn-rate=50 \
    --run-time=10m \
    --headless
```

### Endurance Testing

Test system stability over extended period:

```bash
locust -f tests/load/locustfile.py \
    --host=http://localhost:8000 \
    --users=100 \
    --spawn-rate=10 \
    --run-time=1h \
    --headless
```

### Distributed Load Testing

For very high load, run Locust in distributed mode:

```bash
# Master node
locust -f tests/load/locustfile.py \
    --master \
    --expect-workers=3

# Worker nodes (run on separate machines)
locust -f tests/load/locustfile.py \
    --worker \
    --master-host=<master-ip>
```

## Continuous Integration

To integrate load testing into CI/CD:

```bash
# Run test and check exit code
locust -f tests/load/locustfile.py \
    --host=http://localhost:8000 \
    --users=100 \
    --spawn-rate=10 \
    --run-time=3m \
    --headless \
    --exit-code-on-error=1

# Exit code 0 = success, 1 = failure
```

## Files

- `locustfile.py`: Main load test script
- `config.py`: Test configuration (optional)
- `reports/`: Generated performance reports
- `README.md`: This file

## References

- [Locust Documentation](https://docs.locust.io/)
- [Requirements 18.1-18.6](../../.kiro/specs/architecture-alignment-refactoring/requirements.md)
- [Design: Concurrency Management](../../.kiro/specs/architecture-alignment-refactoring/design.md)
