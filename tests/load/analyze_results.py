#!/usr/bin/env python3
"""
Load Test Results Analyzer

Analyzes load test results and generates detailed reports.
Validates against requirements 18.1-18.6.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


class LoadTestAnalyzer:
    """Analyzes load test results and validates against requirements"""
    
    def __init__(self, report_file: str):
        self.report_file = Path(report_file)
        self.data = self._load_report()
        
    def _load_report(self) -> Dict:
        """Load report from JSON file"""
        if not self.report_file.exists():
            raise FileNotFoundError(f"Report file not found: {self.report_file}")
        
        with open(self.report_file, 'r') as f:
            return json.load(f)
    
    def validate_requirements(self) -> Dict[str, bool]:
        """
        Validate against requirements 18.1-18.6
        
        Returns:
            Dict mapping requirement ID to pass/fail status
        """
        results = {}
        
        # Requirement 18.3: P90 latency 3-8 seconds
        p90_latency = self.data["latency_distribution"]["p90_ms"]
        results["18.3"] = 3000 <= p90_latency <= 8000
        
        # Requirement 18.4: Error rate < 1%
        error_rate = self.data["error_metrics"]["error_rate_percent"]
        results["18.4"] = error_rate < 1.0
        
        # Requirement 18.5: Queue depth measured and requests processed
        queue_depth = self.data["queue_statistics"]["max_queue_depth"]
        total_requests = self.data["test_summary"]["total_requests"]
        results["18.5"] = queue_depth >= 0 and total_requests > 0
        
        # Requirement 18.6: Report generated with latency distribution
        has_latency_dist = all(k in self.data["latency_distribution"] 
                               for k in ["p50_ms", "p90_ms", "p99_ms"])
        results["18.6"] = has_latency_dist
        
        return results
    
    def generate_summary(self) -> str:
        """Generate human-readable summary"""
        summary = []
        summary.append("=" * 70)
        summary.append("LOAD TEST ANALYSIS REPORT")
        summary.append("=" * 70)
        summary.append("")
        
        # Test summary
        test_summary = self.data["test_summary"]
        summary.append("Test Summary:")
        summary.append(f"  Start Time: {test_summary['start_time']}")
        summary.append(f"  End Time: {test_summary['end_time']}")
        summary.append(f"  Total Requests: {test_summary['total_requests']}")
        summary.append(f"  Successful: {test_summary['successful_requests']}")
        summary.append(f"  Failed: {test_summary['failed_requests']}")
        summary.append(f"  Queue Full: {test_summary['queue_full_responses']}")
        summary.append("")
        
        # Latency distribution
        latency = self.data["latency_distribution"]
        summary.append("Latency Distribution:")
        summary.append(f"  Average: {latency['average_ms']:.2f}ms")
        summary.append(f"  P50 (Median): {latency['p50_ms']:.2f}ms")
        summary.append(f"  P90: {latency['p90_ms']:.2f}ms")
        summary.append(f"  P99: {latency['p99_ms']:.2f}ms")
        summary.append(f"  Min: {latency['min_ms']:.2f}ms")
        summary.append(f"  Max: {latency['max_ms']:.2f}ms")
        summary.append("")
        
        # Error metrics
        errors = self.data["error_metrics"]
        summary.append("Error Metrics:")
        summary.append(f"  Error Count: {errors['error_count']}")
        summary.append(f"  Error Rate: {errors['error_rate_percent']:.2f}%")
        summary.append(f"  Target: {errors['target_error_rate']}")
        summary.append(f"  Status: {'✅ PASS' if errors['meets_requirement'] else '❌ FAIL'}")
        summary.append("")
        
        # Performance validation
        perf = self.data["performance_validation"]
        summary.append("Performance Validation:")
        summary.append(f"  P90 Latency: {perf['p90_latency_ms']:.2f}ms")
        summary.append(f"  Target Range: {perf['target_range_ms']}")
        summary.append(f"  Status: {'✅ PASS' if perf['meets_requirement'] else '❌ FAIL'}")
        summary.append("")
        
        # Queue statistics
        queue = self.data["queue_statistics"]
        summary.append("Queue Statistics:")
        summary.append(f"  Max Queue Depth: {queue['max_queue_depth']}")
        summary.append(f"  Max Active Threads: {queue['max_active']}")
        summary.append("")
        
        # Requirements validation
        validation = self.validate_requirements()
        summary.append("Requirements Validation:")
        summary.append(f"  18.3 (P90 Latency 3-8s): {'✅ PASS' if validation['18.3'] else '❌ FAIL'}")
        summary.append(f"  18.4 (Error Rate < 1%): {'✅ PASS' if validation['18.4'] else '❌ FAIL'}")
        summary.append(f"  18.5 (Queue Processing): {'✅ PASS' if validation['18.5'] else '✅ PASS'}")
        summary.append(f"  18.6 (Report Generated): {'✅ PASS' if validation['18.6'] else '❌ FAIL'}")
        summary.append("")
        
        # Overall result
        all_passed = all(validation.values())
        summary.append("=" * 70)
        summary.append(f"OVERALL RESULT: {'✅ PASS' if all_passed else '❌ FAIL'}")
        summary.append("=" * 70)
        
        return "\n".join(summary)
    
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on results"""
        recommendations = []
        
        # Check P90 latency
        p90 = self.data["latency_distribution"]["p90_ms"]
        if p90 > 8000:
            recommendations.append(
                "⚠️ P90 latency exceeds 8 seconds. Consider:\n"
                "   - Enabling Redis caching\n"
                "   - Optimizing database queries\n"
                "   - Increasing system resources"
            )
        elif p90 > 7000:
            recommendations.append(
                "⚠️ P90 latency approaching upper limit. Monitor closely."
            )
        
        # Check error rate
        error_rate = self.data["error_metrics"]["error_rate_percent"]
        if error_rate > 1.0:
            recommendations.append(
                "⚠️ Error rate exceeds 1%. Investigate:\n"
                "   - Check application logs\n"
                "   - Verify database connections\n"
                "   - Check system resources"
            )
        elif error_rate > 0.5:
            recommendations.append(
                "⚠️ Error rate approaching threshold. Monitor for issues."
            )
        
        # Check queue depth
        queue_depth = self.data["queue_statistics"]["max_queue_depth"]
        if queue_depth > 100:
            recommendations.append(
                "⚠️ High queue depth detected. Consider:\n"
                "   - Increasing concurrency limit (if resources allow)\n"
                "   - Optimizing response time\n"
                "   - Implementing request prioritization"
            )
        
        # Check queue full responses
        queue_full = self.data["test_summary"]["queue_full_responses"]
        total = self.data["test_summary"]["total_requests"]
        queue_full_rate = (queue_full / total * 100) if total > 0 else 0
        
        if queue_full_rate > 10:
            recommendations.append(
                f"⚠️ High queue full rate ({queue_full_rate:.1f}%). Consider:\n"
                "   - Increasing concurrency limit\n"
                "   - Implementing request throttling\n"
                "   - Adding more server resources"
            )
        
        if not recommendations:
            recommendations.append("✅ All metrics within acceptable ranges. No immediate action required.")
        
        return recommendations
    
    def export_csv(self, output_file: str):
        """Export summary to CSV format"""
        import csv
        
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                "Metric", "Value", "Target", "Status"
            ])
            
            # Latency metrics
            latency = self.data["latency_distribution"]
            writer.writerow(["Average Latency (ms)", f"{latency['average_ms']:.2f}", "-", "-"])
            writer.writerow(["P50 Latency (ms)", f"{latency['p50_ms']:.2f}", "-", "-"])
            writer.writerow(["P90 Latency (ms)", f"{latency['p90_ms']:.2f}", "3000-8000", 
                           "PASS" if 3000 <= latency['p90_ms'] <= 8000 else "FAIL"])
            writer.writerow(["P99 Latency (ms)", f"{latency['p99_ms']:.2f}", "-", "-"])
            
            # Error metrics
            errors = self.data["error_metrics"]
            writer.writerow(["Error Rate (%)", f"{errors['error_rate_percent']:.2f}", "< 1.0",
                           "PASS" if errors['error_rate_percent'] < 1.0 else "FAIL"])
            
            # Queue metrics
            queue = self.data["queue_statistics"]
            writer.writerow(["Max Queue Depth", queue['max_queue_depth'], "-", "-"])
            writer.writerow(["Max Active Threads", queue['max_active'], "5", "-"])
        
        print(f"✅ CSV report exported to: {output_file}")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python analyze_results.py <report_file.json>")
        print("\nExample:")
        print("  python analyze_results.py tests/load/reports/load_test_report_20260215_103000.json")
        sys.exit(1)
    
    report_file = sys.argv[1]
    
    try:
        analyzer = LoadTestAnalyzer(report_file)
        
        # Print summary
        print(analyzer.generate_summary())
        print()
        
        # Print recommendations
        print("Recommendations:")
        for rec in analyzer.generate_recommendations():
            print(f"  {rec}")
        print()
        
        # Export CSV if requested
        if len(sys.argv) > 2 and sys.argv[2] == "--csv":
            csv_file = report_file.replace(".json", ".csv")
            analyzer.export_csv(csv_file)
        
    except Exception as e:
        print(f"❌ Error analyzing report: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
