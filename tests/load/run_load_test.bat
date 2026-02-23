@echo off
REM Quick start script for running load tests on Windows

echo ======================================================================
echo OpenClass Nexus AI - Load Testing Suite
echo ======================================================================
echo.

REM Check if Locust is installed
where locust >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: Locust is not installed.
    echo.
    echo Install with:
    echo   pip install locust
    echo.
    exit /b 1
)

REM Check if server is running
curl -s http://localhost:8000/api/health >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: Server is not running at http://localhost:8000
    echo.
    echo Start the server with:
    echo   python api_server.py
    echo.
    exit /b 1
)

echo Server is running
echo.

REM Create reports directory
if not exist tests\load\reports mkdir tests\load\reports

REM Parse command line arguments
set TEST_SCENARIO=%1
if "%TEST_SCENARIO%"=="" set TEST_SCENARIO=normal

set MODE=%2
if "%MODE%"=="" set MODE=web

if "%TEST_SCENARIO%"=="light" (
    set USERS=50
    set SPAWN_RATE=5
    set RUN_TIME=3m
    set DESCRIPTION=Light Load (50 users^)
) else if "%TEST_SCENARIO%"=="normal" (
    set USERS=100
    set SPAWN_RATE=10
    set RUN_TIME=5m
    set DESCRIPTION=Normal Load (100 users^) - Requirement 18.1
) else if "%TEST_SCENARIO%"=="heavy" (
    set USERS=300
    set SPAWN_RATE=20
    set RUN_TIME=5m
    set DESCRIPTION=Heavy Load (300 users^) - Requirement 18.2
) else if "%TEST_SCENARIO%"=="stress" (
    set USERS=500
    set SPAWN_RATE=50
    set RUN_TIME=10m
    set DESCRIPTION=Stress Test (500 users^)
) else if "%TEST_SCENARIO%"=="endurance" (
    set USERS=100
    set SPAWN_RATE=10
    set RUN_TIME=1h
    set DESCRIPTION=Endurance Test (100 users for 1 hour^)
) else (
    echo Error: Unknown test scenario: %TEST_SCENARIO%
    echo.
    echo Available scenarios:
    echo   light     - 50 concurrent users
    echo   normal    - 100 concurrent users (Requirement 18.1^)
    echo   heavy     - 300 concurrent users (Requirement 18.2^)
    echo   stress    - 500 concurrent users
    echo   endurance - 100 users for 1 hour
    echo.
    echo Usage:
    echo   run_load_test.bat [scenario] [mode]
    echo.
    echo Examples:
    echo   run_load_test.bat normal web      # Run normal load test with web UI
    echo   run_load_test.bat heavy headless  # Run heavy load test in headless mode
    echo.
    exit /b 1
)

echo ======================================================================
echo Test Configuration:
echo   Scenario: %DESCRIPTION%
echo   Users: %USERS%
echo   Spawn Rate: %SPAWN_RATE% users/second
echo   Run Time: %RUN_TIME%
echo   Mode: %MODE%
echo ======================================================================
echo.

if "%MODE%"=="web" (
    echo Starting Locust Web UI...
    echo.
    echo Open your browser and go to: http://localhost:8089
    echo.
    echo Configure the test with:
    echo   - Number of users: %USERS%
    echo   - Spawn rate: %SPAWN_RATE%
    echo   - Host: http://localhost:8000
    echo.
    echo Press Ctrl+C to stop the test
    echo.
    
    locust -f tests/load/locustfile.py --host=http://localhost:8000
) else (
    echo Running load test in headless mode...
    echo.
    
    locust -f tests/load/locustfile.py ^
        --host=http://localhost:8000 ^
        --users=%USERS% ^
        --spawn-rate=%SPAWN_RATE% ^
        --run-time=%RUN_TIME% ^
        --headless
    
    echo.
    echo ======================================================================
    echo Test completed!
    echo.
    echo Check the report in: tests\load\reports\
    echo.
    echo To analyze results:
    echo   python tests\load\analyze_results.py tests\load\reports\^<report_file^>.json
    echo ======================================================================
)
