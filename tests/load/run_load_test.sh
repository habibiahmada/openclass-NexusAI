#!/bin/bash
# Quick start script for running load tests

set -e

echo "======================================================================"
echo "OpenClass Nexus AI - Load Testing Suite"
echo "======================================================================"
echo ""

# Check if Locust is installed
if ! command -v locust &> /dev/null; then
    echo "❌ Locust is not installed."
    echo ""
    echo "Install with:"
    echo "  pip install locust"
    echo ""
    exit 1
fi

# Check if server is running
echo "Checking if server is running..."
if ! curl -s http://localhost:8000/api/health > /dev/null; then
    echo "❌ Server is not running at http://localhost:8000"
    echo ""
    echo "Start the server with:"
    echo "  python api_server.py"
    echo ""
    exit 1
fi

echo "✅ Server is running"
echo ""

# Create reports directory
mkdir -p tests/load/reports

# Parse command line arguments
TEST_SCENARIO=${1:-"normal_load"}
MODE=${2:-"web"}

case $TEST_SCENARIO in
    "light")
        USERS=50
        SPAWN_RATE=5
        RUN_TIME="3m"
        DESCRIPTION="Light Load (50 users)"
        ;;
    "normal")
        USERS=100
        SPAWN_RATE=10
        RUN_TIME="5m"
        DESCRIPTION="Normal Load (100 users) - Requirement 18.1"
        ;;
    "heavy")
        USERS=300
        SPAWN_RATE=20
        RUN_TIME="5m"
        DESCRIPTION="Heavy Load (300 users) - Requirement 18.2"
        ;;
    "stress")
        USERS=500
        SPAWN_RATE=50
        RUN_TIME="10m"
        DESCRIPTION="Stress Test (500 users)"
        ;;
    "endurance")
        USERS=100
        SPAWN_RATE=10
        RUN_TIME="1h"
        DESCRIPTION="Endurance Test (100 users for 1 hour)"
        ;;
    *)
        echo "❌ Unknown test scenario: $TEST_SCENARIO"
        echo ""
        echo "Available scenarios:"
        echo "  light     - 50 concurrent users"
        echo "  normal    - 100 concurrent users (Requirement 18.1)"
        echo "  heavy     - 300 concurrent users (Requirement 18.2)"
        echo "  stress    - 500 concurrent users"
        echo "  endurance - 100 users for 1 hour"
        echo ""
        echo "Usage:"
        echo "  ./run_load_test.sh [scenario] [mode]"
        echo ""
        echo "Examples:"
        echo "  ./run_load_test.sh normal web      # Run normal load test with web UI"
        echo "  ./run_load_test.sh heavy headless  # Run heavy load test in headless mode"
        echo ""
        exit 1
        ;;
esac

echo "======================================================================"
echo "Test Configuration:"
echo "  Scenario: $DESCRIPTION"
echo "  Users: $USERS"
echo "  Spawn Rate: $SPAWN_RATE users/second"
echo "  Run Time: $RUN_TIME"
echo "  Mode: $MODE"
echo "======================================================================"
echo ""

if [ "$MODE" = "web" ]; then
    echo "Starting Locust Web UI..."
    echo ""
    echo "Open your browser and go to: http://localhost:8089"
    echo ""
    echo "Configure the test with:"
    echo "  - Number of users: $USERS"
    echo "  - Spawn rate: $SPAWN_RATE"
    echo "  - Host: http://localhost:8000"
    echo ""
    echo "Press Ctrl+C to stop the test"
    echo ""
    
    locust -f tests/load/locustfile.py \
        --host=http://localhost:8000
else
    echo "Running load test in headless mode..."
    echo ""
    
    locust -f tests/load/locustfile.py \
        --host=http://localhost:8000 \
        --users=$USERS \
        --spawn-rate=$SPAWN_RATE \
        --run-time=$RUN_TIME \
        --headless
    
    echo ""
    echo "======================================================================"
    echo "Test completed!"
    echo ""
    echo "Check the report in: tests/load/reports/"
    echo ""
    echo "To analyze results:"
    echo "  python tests/load/analyze_results.py tests/load/reports/<report_file>.json"
    echo "======================================================================"
fi
