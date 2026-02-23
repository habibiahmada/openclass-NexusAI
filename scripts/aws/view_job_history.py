#!/usr/bin/env python3
"""
View ETL Pipeline Job History

Query DynamoDB to view recent pipeline runs, costs, and statistics.
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from src.aws_control_plane.job_tracker import JobTracker, DecimalEncoder

load_dotenv()


def format_job(job: dict) -> str:
    """Format job dict for display"""
    lines = []
    lines.append(f"\n{'='*60}")
    lines.append(f"Job ID: {job.get('job_id', 'N/A')}")
    lines.append(f"Status: {job.get('status', 'N/A')}")
    lines.append(f"Started: {job.get('started_at', 'N/A')}")
    
    if 'completed_at' in job:
        lines.append(f"Completed: {job['completed_at']}")
    
    lines.append(f"\nProcessing:")
    lines.append(f"  Total files: {job.get('total_files', 0)}")
    lines.append(f"  Successful: {job.get('successful_files', 0)}")
    lines.append(f"  Failed: {job.get('failed_files', 0)}")
    lines.append(f"  Chunks: {job.get('total_chunks', 0)}")
    lines.append(f"  Embeddings: {job.get('total_embeddings', 0)}")
    
    lines.append(f"\nPerformance:")
    lines.append(f"  Processing time: {job.get('processing_time', 0):.2f}s")
    lines.append(f"  Estimated cost: ${job.get('estimated_cost', 0):.4f}")
    
    if 'errors' in job and job['errors']:
        try:
            errors = json.loads(job['errors']) if isinstance(job['errors'], str) else job['errors']
            lines.append(f"\nErrors ({len(errors)}):")
            for error in errors[:3]:  # Show first 3 errors
                lines.append(f"  - {error}")
            if len(errors) > 3:
                lines.append(f"  ... and {len(errors) - 3} more")
        except:
            pass
    
    lines.append(f"{'='*60}")
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='View ETL pipeline job history from DynamoDB'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=10,
        help='Number of recent jobs to show (default: 10)'
    )
    
    parser.add_argument(
        '--status',
        type=str,
        choices=['running', 'completed', 'failed', 'partial'],
        help='Filter by job status'
    )
    
    parser.add_argument(
        '--job-id',
        type=str,
        help='Get specific job by ID'
    )
    
    parser.add_argument(
        '--cost-summary',
        action='store_true',
        help='Show cost summary for last 7 days'
    )
    
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output as JSON'
    )
    
    args = parser.parse_args()
    
    try:
        tracker = JobTracker()
        
        # Get specific job
        if args.job_id:
            job = tracker.get_job(args.job_id)
            if job:
                if args.json:
                    print(json.dumps(job, indent=2, cls=DecimalEncoder))
                else:
                    print(format_job(job))
            else:
                print(f"Job not found: {args.job_id}")
                return 1
        
        # Show cost summary
        elif args.cost_summary:
            summary = tracker.get_cost_summary(days=7)
            if args.json:
                print(json.dumps(summary, indent=2, cls=DecimalEncoder))
            else:
                print("\n" + "="*60)
                print("Cost Summary (Last 7 Days)")
                print("="*60)
                print(f"Total jobs: {summary['total_jobs']}")
                print(f"Total cost: ${summary['total_cost']:.4f}")
                print(f"Average cost per job: ${summary['average_cost_per_job']:.4f}")
                print(f"Total files processed: {summary['total_files_processed']}")
                print(f"Total embeddings: {summary['total_embeddings_generated']}")
                print(f"Cost per file: ${summary['cost_per_file']:.6f}")
                print(f"Cost per embedding: ${summary['cost_per_embedding']:.8f}")
                print("="*60)
        
        # List jobs
        else:
            if args.status:
                jobs = tracker.get_jobs_by_status(args.status, limit=args.limit)
                print(f"\nJobs with status '{args.status}' (limit: {args.limit}):")
            else:
                jobs = tracker.list_recent_jobs(limit=args.limit)
                print(f"\nRecent jobs (limit: {args.limit}):")
            
            if not jobs:
                print("No jobs found.")
                return 0
            
            if args.json:
                print(json.dumps(jobs, indent=2, cls=DecimalEncoder))
            else:
                for job in jobs:
                    print(format_job(job))
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
