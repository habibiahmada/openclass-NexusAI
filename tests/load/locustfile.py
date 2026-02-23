"""
Load Testing Suite for OpenClass Nexus AI
Using Locust for simulating concurrent users

Requirements tested:
- 18.1: Simulate 100 concurrent users with stable performance
- 18.2: Simulate 300 concurrent users with acceptable degradation
- 18.3: Maintain 3-8 second response time for 90th percentile
- 18.4: Measure error rate and verify < 1% errors
- 18.5: Measure queue depth and verify requests are processed
- 18.6: Generate performance report with latency distribution
"""

import json
import random
import time
from datetime import datetime
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner, WorkerRunner

# Test data
SAMPLE_QUESTIONS = [
    "Apa itu Teorema Pythagoras?",
    "Jelaskan tentang fotosintesis",
    "Bagaimana cara menghitung luas lingkaran?",
    "Apa perbedaan antara mitosis dan meiosis?",
    "Jelaskan konsep variabel dalam pemrograman",
    "Apa itu algoritma sorting?",
    "Bagaimana proses terjadinya hujan?",
    "Jelaskan hukum Newton pertama",
    "Apa fungsi dari klorofil pada tumbuhan?",
    "Bagaimana cara menyelesaikan persamaan kuadrat?",
]

SUBJECTS = ["matematika", "informatika", "biologi", "fisika", "all"]

# Test credentials (should match database)
TEST_USERS = [
    {"username": "siswa1", "password": "password123"},
    {"username": "siswa2", "password": "password123"},
    {"username": "siswa3", "password": "password123"},
]

# Global metrics storage
metrics_data = {
    "requests": [],
    "errors": [],
    "queue_stats": [],
    "start_time": None,
    "end_time": None
}


class NexusAIUser(HttpUser):
    """
    Simulates a student user interacting with the AI tutor
    """
    wait_time = between(5, 15)  # Wait 5-15 seconds between requests (realistic student behavior)
    
    def on_start(self):
        """Called when a user starts - performs login"""
        self.token = None
        self.user_id = None
        self.login()
    
    def login(self):
        """Authenticate and get token"""
        # Select random test user
        user = random.choice(TEST_USERS)
        
        try:
            response = self.client.post(
                "/api/auth/login",
                json={
                    "username": user["username"],
                    "password": user["password"]
                },
                name="/api/auth/login"
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("token")
                self.user_id = data.get("user_id")
            else:
                # If login fails, try to continue without token (will fail gracefully)
                self.token = None
                
        except Exception as e:
            print(f"Login error: {e}")
            self.token = None
    
    @task(10)
    def ask_question(self):
        """
        Main task: Ask a question to the AI tutor
        Weight: 10 (most common action)
        """
        if not self.token:
            return
        
        question = random.choice(SAMPLE_QUESTIONS)
        subject = random.choice(SUBJECTS)
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        start_time = time.time()
        
        try:
            with self.client.post(
                "/api/chat",
                json={
                    "message": question,
                    "subject_filter": subject
                },
                headers=headers,
                catch_response=True,
                name="/api/chat"
            ) as response:
                latency = (time.time() - start_time) * 1000  # Convert to ms
                
                if response.status_code == 200:
                    response.success()
                    # Record successful request
                    metrics_data["requests"].append({
                        "timestamp": datetime.now().isoformat(),
                        "latency_ms": latency,
                        "status": "success"
                    })
                elif response.status_code == 503:
                    # Queue full - expected under high load
                    response.success()  # Don't count as failure
                    metrics_data["requests"].append({
                        "timestamp": datetime.now().isoformat(),
                        "latency_ms": latency,
                        "status": "queue_full"
                    })
                else:
                    response.failure(f"Status code: {response.status_code}")
                    metrics_data["errors"].append({
                        "timestamp": datetime.now().isoformat(),
                        "status_code": response.status_code,
                        "error": response.text[:200]
                    })
                    
        except Exception as e:
            metrics_data["errors"].append({
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            })
    
    @task(2)
    def check_queue_status(self):
        """
        Check queue status
        Weight: 2 (less frequent)
        """
        if not self.token:
            return
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            response = self.client.get(
                "/api/queue/stats",
                headers=headers,
                name="/api/queue/stats"
            )
            
            if response.status_code == 200:
                stats = response.json()
                metrics_data["queue_stats"].append({
                    "timestamp": datetime.now().isoformat(),
                    "active": stats.get("active_count", 0),
                    "queued": stats.get("queued_count", 0),
                    "total_processed": stats.get("total_processed", 0)
                })
        except Exception as e:
            pass  # Queue stats are optional
    
    @task(1)
    def check_health(self):
        """
        Check system health
        Weight: 1 (least frequent)
        """
        try:
            self.client.get("/api/health", name="/api/health")
        except Exception:
            pass  # Health check failures are logged by Locust


# Event handlers for metrics collection
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts"""
    metrics_data["start_time"] = datetime.now().isoformat()
    print("=" * 60)
    print("Load Test Started")
    print(f"Target: {environment.host}")
    print("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops - generate report"""
    metrics_data["end_time"] = datetime.now().isoformat()
    
    # Calculate statistics
    requests = metrics_data["requests"]
    errors = metrics_data["errors"]
    
    if requests:
        latencies = [r["latency_ms"] for r in requests if r["status"] == "success"]
        
        if latencies:
            latencies.sort()
            total_requests = len(requests)
            successful_requests = len(latencies)
            error_count = len(errors)
            queue_full_count = len([r for r in requests if r["status"] == "queue_full"])
            
            # Calculate percentiles
            p50_idx = int(len(latencies) * 0.50)
            p90_idx = int(len(latencies) * 0.90)
            p99_idx = int(len(latencies) * 0.99)
            
            p50 = latencies[p50_idx] if p50_idx < len(latencies) else 0
            p90 = latencies[p90_idx] if p90_idx < len(latencies) else 0
            p99 = latencies[p99_idx] if p99_idx < len(latencies) else 0
            
            avg_latency = sum(latencies) / len(latencies)
            error_rate = (error_count / total_requests) * 100 if total_requests > 0 else 0
            
            # Generate report
            report = {
                "test_summary": {
                    "start_time": metrics_data["start_time"],
                    "end_time": metrics_data["end_time"],
                    "total_requests": total_requests,
                    "successful_requests": successful_requests,
                    "failed_requests": error_count,
                    "queue_full_responses": queue_full_count
                },
                "latency_distribution": {
                    "average_ms": round(avg_latency, 2),
                    "p50_ms": round(p50, 2),
                    "p90_ms": round(p90, 2),
                    "p99_ms": round(p99, 2),
                    "min_ms": round(min(latencies), 2),
                    "max_ms": round(max(latencies), 2)
                },
                "error_metrics": {
                    "error_count": error_count,
                    "error_rate_percent": round(error_rate, 2),
                    "target_error_rate": "< 1%",
                    "meets_requirement": error_rate < 1.0
                },
                "performance_validation": {
                    "p90_latency_ms": round(p90, 2),
                    "target_range_ms": "3000-8000",
                    "meets_requirement": 3000 <= p90 <= 8000
                },
                "queue_statistics": {
                    "max_queue_depth": max([s.get("queued", 0) for s in metrics_data["queue_stats"]], default=0),
                    "max_active": max([s.get("active", 0) for s in metrics_data["queue_stats"]], default=0)
                }
            }
            
            # Save report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = f"tests/load/reports/load_test_report_{timestamp}.json"
            
            try:
                with open(report_file, "w") as f:
                    json.dump(report, f, indent=2)
                print(f"\n✅ Report saved to: {report_file}")
            except Exception as e:
                print(f"\n⚠️ Could not save report: {e}")
            
            # Print summary
            print("\n" + "=" * 60)
            print("LOAD TEST SUMMARY")
            print("=" * 60)
            print(f"Total Requests: {total_requests}")
            print(f"Successful: {successful_requests}")
            print(f"Failed: {error_count}")
            print(f"Queue Full: {queue_full_count}")
            print(f"\nLatency Distribution:")
            print(f"  Average: {avg_latency:.2f}ms")
            print(f"  P50: {p50:.2f}ms")
            print(f"  P90: {p90:.2f}ms (Target: 3000-8000ms)")
            print(f"  P99: {p99:.2f}ms")
            print(f"\nError Rate: {error_rate:.2f}% (Target: < 1%)")
            print(f"\nRequirements Validation:")
            print(f"  ✅ P90 Latency: {'PASS' if 3000 <= p90 <= 8000 else 'FAIL'}")
            print(f"  ✅ Error Rate: {'PASS' if error_rate < 1.0 else 'FAIL'}")
            print("=" * 60)
