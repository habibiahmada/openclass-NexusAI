"""
Load Testing Suite for OpenClass Nexus AI

This package contains load testing tools and scripts for validating
system performance under concurrent user load.

Requirements tested:
- 18.1: Simulate 100 concurrent users with stable performance
- 18.2: Simulate 300 concurrent users with acceptable degradation
- 18.3: Maintain 3-8 second response time for 90th percentile
- 18.4: Measure error rate and verify < 1% errors
- 18.5: Measure queue depth and verify requests are processed
- 18.6: Generate performance report with latency distribution
"""

__version__ = "1.0.0"
