# Load Testing Guide for OpenClass Nexus AI

## Overview

This guide provides comprehensive information about load testing the OpenClass Nexus AI system to validate performance requirements under concurrent user load.

## Architecture Context

### System Capacity

The OpenClass Nexus AI system is designed to run on school servers with the following specifications:

- **Hardware**: 16GB RAM, 8-core CPU, 512GB SSD
- **Concurrency Limit**: 5 concurrent inference threads
- **Target Latency**: 3-8 seconds per response (P90)
- **Expected Throughput**: ~1 request/second = 60 requests/minute

### Load Scenarios

#### Scenario 1: 100 Concurrent Users (Requirement 18.1)

- **Utilization**: ~16.7% (comfortable)
- **Expected Behavior**: Stable performance, minimal queuing
- **Validation**: P90 latency 3-8s, error rate < 1%

**Calculation**:
- If each student asks 1 question every 10 minutes
- Load = 100 students / 10 minutes = 10 requests/minute
- Utilization = 10 / 60 = 16.7%

#### Scenario 2: 300 Concurrent Users (Requirement 18.2)

- **Utilization**: ~50% (acceptable)
- **Expected Behavior**: Acceptable degradation, moderate queuing
- **Validation**: P90 latency 3-8s, error rate < 1%

**Calculation**:
- Load = 300 students / 10 minutes = 30 requests/minute
- Utilization = 30 / 60 = 50%

## Requirements Validation

### Requirement 18.1: 100 Concurrent Users

**Requirement**: THE Load_Testing_Suite SHALL simulate 100 concurrent users with stable performance

**Test Approach**:
- Spawn 100 Locust users at 10 users/second
- Each user asks questions every 5-15 seconds (realistic behavior)
- Run for 5 minutes to collect sufficient data
- Measure latency distribution and error rate

**Success Criteria**:
- P90 latency: 3000-8000ms
- Error rate: < 1%
- System remains stable throughout test
- No service crashes or failures

### Requirement 18.2: 300 Concurrent Users

**Requirement**: THE Load_Testing_Suite SHALL simulate 300 concurrent users with acceptable degradation

**Test Approach**:
- Spawn 300 Locust users at 20 users/second
- Each user asks questions every 5-15 seconds
- Run for 5 minutes to collect sufficient data
- Measure latency distribution and error rate

**Success Criteria**:
- P90 latency: 3000-8000ms (acceptable degradation)
- Error rate: < 1%
- Queue depth: moderate (10-50)
- Some 503 responses (queue full) are acceptable

### Requirement 18.3: Response Time

**Requirement**: WHEN load testing runs, THE System SHALL maintain 3-8 second response time for 90th percentile

**Test Approach**:
- Measure response time for every request
- Calculate P50, P90, P99 percentiles
- Validate P90 is within 3000-8000ms range

**Validation**:
```python
p90_latency = calculate_percentile(latencies, 0.90)
assert 3000 <= p90_latency <= 8000, "P90 latency out of range"
```

### Requirement 18.4: Error Rate

**Requirement**: THE Load_Testing_Suite SHALL measure error rate and verify < 1% errors

**Test Approach**:
- Track all HTTP responses
- Count 4xx and 5xx errors (excluding 503 queue full)
- Calculate error rate as percentage of total requests

**Validation**:
```python
error_rate = (error_count / total_requests) * 100
assert error_rate < 1.0, "Error rate exceeds 1%"
```

### Requirement 18.5: Queue Depth

**Requirement**: THE Load_Testing_Suite SHALL measure queue depth and verify requests are processed

**Test Approach**:
- Periodically query `/api/queue/stats` endpoint
- Record active threads and queued requests
- Verify requests are being processed (not stuck)

**Validation**:
- Queue depth is measured and recorded
- Total processed requests > 0
- Queue depth fluctuates (not stuck at max)

### Requirement 18.6: Performance Report

**Requirement**: THE Load_Testing_Suite SHALL generate performance report with latency distribution

**Test Approach**:
- Collect all request metrics during test
- Generate JSON report with:
  - Test summary (start/end time, request counts)
  - Latency distribution (avg, P50, P90, P99, min, max)
  - Error metrics (count, rate, validation)
  - Queue statistics (max depth, max active)

**Report Format**:
```json
{
  "test_summary": {...},
  "latency_distribution": {
    "average_ms": 4500,
    "p50_ms": 4200,
    "p90_ms": 6200,
    "p99_ms": 7800
  },
  "error_metrics": {...},
  "queue_statistics": {...}
}
```

## Test Execution

### Prerequisites

1. **Install Locust**:
   ```bash
   pip install locust
   ```

2. **Start Server**:
   ```bash
   python api_server.py
   ```

3. **Create Test Users**:
   ```bash
   python tests/load/setup_test_users.py
   ```

### Running Tests

#### Quick Start (Recommended)

**Linux/Mac**:
```bash
# Make script executable
chmod +x tests/load/run_load_test.sh

# Run normal load test (100 users)
./tests/load/run_load_test.sh normal web

# Run heavy load test (300 users)
./tests/load/run_load_test.sh heavy headless
```

**Windows**:
```cmd
REM Run normal load test (100 users)
tests\load\run_load_test.bat normal web

REM Run heavy load test (300 users)
tests\load\run_load_test.bat heavy headless
```

#### Manual Execution

**Test 1: 100 Concurrent Users**:
```bash
locust -f tests/load/locustfile.py \
    --host=http://localhost:8000 \
    --users=100 \
    --spawn-rate=10 \
    --run-time=5m \
    --headless
```

**Test 2: 300 Concurrent Users**:
```bash
locust -f tests/load/locustfile.py \
    --host=http://localhost:8000 \
    --users=300 \
    --spawn-rate=20 \
    --run-time=5m \
    --headless
```

### Analyzing Results

After running a test, analyze the results:

```bash
# Find the latest report
ls -lt tests/load/reports/

# Analyze report
python tests/load/analyze_results.py tests/load/reports/load_test_report_YYYYMMDD_HHMMSS.json

# Export to CSV
python tests/load/analyze_results.py tests/load/reports/load_test_report_YYYYMMDD_HHMMSS.json --csv
```

## Understanding Results

### Locust Web UI

When running in web UI mode (http://localhost:8089), you'll see:

1. **Statistics Tab**:
   - Request count and failure rate
   - Response times (min, max, average, median)
   - Requests per second
   - Response time percentiles

2. **Charts Tab**:
   - Total requests per second over time
   - Response times over time
   - Number of users over time

3. **Failures Tab**:
   - Failed requests with error messages
   - Useful for debugging issues

4. **Download Data**:
   - Export results as CSV for further analysis

### Performance Report

The JSON report contains:

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

### Interpreting Metrics

#### Latency Distribution

- **Average**: Mean response time across all requests
- **P50 (Median)**: 50% of requests complete faster than this
- **P90**: 90% of requests complete faster than this (our target metric)
- **P99**: 99% of requests complete faster than this
- **Min/Max**: Fastest and slowest requests

**Good**: P90 between 3000-8000ms
**Warning**: P90 approaching 8000ms
**Bad**: P90 > 8000ms

#### Error Rate

- **Error Count**: Number of failed requests (4xx, 5xx errors)
- **Error Rate**: Percentage of failed requests
- **Target**: < 1%

**Note**: 503 (Queue Full) responses are tracked separately and are acceptable under high load.

#### Queue Statistics

- **Max Queue Depth**: Maximum number of requests waiting in queue
- **Max Active**: Maximum concurrent threads (should be 5)

**Good**: Queue depth < 50
**Warning**: Queue depth 50-100
**Bad**: Queue depth > 100 (potential bottleneck)

## Troubleshooting

### High Latency (P90 > 8000ms)

**Possible Causes**:
1. CPU overload
2. Memory pressure
3. Slow database queries
4. ChromaDB performance issues
5. LLM inference bottleneck

**Investigation Steps**:

1. **Check System Resources**:
   ```bash
   # CPU usage
   top
   htop
   
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

3. **Check Application Logs**:
   ```bash
   tail -f logs/api_server.log
   ```

**Solutions**:
- Enable Redis caching
- Optimize database queries
- Increase system resources
- Reduce LLM max_tokens
- Optimize ChromaDB collection

### High Error Rate (> 1%)

**Possible Causes**:
1. Database connection pool exhaustion
2. Application errors
3. System resource exhaustion
4. Network issues

**Investigation Steps**:

1. **Check Error Types**:
   - Look at Locust Failures tab
   - Check application logs
   - Identify error patterns

2. **Check Database**:
   ```bash
   # Connection pool status
   psql -U nexusai -d nexusai_school -c "SELECT * FROM pg_stat_activity;"
   ```

3. **Check System Health**:
   ```bash
   curl http://localhost:8000/api/health
   ```

**Solutions**:
- Increase database connection pool size
- Fix application bugs
- Add error handling
- Implement retry logic

### Queue Full (Many 503 Errors)

**Expected Behavior**:
- Some 503 errors are acceptable under 300 concurrent users
- Indicates system is at capacity

**If Excessive**:

1. **Increase Concurrency Limit** (if resources allow):
   ```python
   # config/app_config.py
   max_concurrent_threads = 7  # Increase from 5
   ```

2. **Optimize Response Time**:
   - Enable caching
   - Optimize queries
   - Reduce inference time

3. **Implement Request Prioritization**:
   - Priority queue for teacher requests
   - Throttling for excessive users

## Best Practices

### Test Environment

1. **Dedicated Test Server**: Run tests on a server similar to production
2. **Clean State**: Start with fresh database and cache
3. **Realistic Data**: Use representative curriculum data
4. **Network Conditions**: Test on LAN (not localhost)

### Test Execution

1. **Warm-up Period**: Allow system to warm up before measuring
2. **Sufficient Duration**: Run for at least 5 minutes
3. **Multiple Runs**: Run tests multiple times for consistency
4. **Baseline**: Establish baseline performance before changes

### Result Analysis

1. **Compare Runs**: Compare results across different runs
2. **Trend Analysis**: Look for performance trends over time
3. **Percentiles**: Focus on P90/P99, not just average
4. **Error Patterns**: Analyze error types and patterns

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
if [ $? -eq 0 ]; then
    echo "✅ Load test passed"
else
    echo "❌ Load test failed"
    exit 1
fi
```

## References

- [Locust Documentation](https://docs.locust.io/)
- [Requirements 18.1-18.6](../../.kiro/specs/architecture-alignment-refactoring/requirements.md)
- [Design: Concurrency Management](../../.kiro/specs/architecture-alignment-refactoring/design.md)
- [Design: Load Testing](../../.kiro/specs/architecture-alignment-refactoring/design.md#load-testing)

## Support

For issues or questions:
1. Check application logs: `logs/api_server.log`
2. Check system health: `curl http://localhost:8000/api/health`
3. Review troubleshooting section above
4. Consult design documentation
