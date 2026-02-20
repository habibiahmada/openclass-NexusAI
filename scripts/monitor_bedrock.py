#!/usr/bin/env python3
"""
Script untuk monitoring AWS Bedrock usage dan metrics
"""

import sys
import boto3
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.aws_config import aws_config

load_dotenv()


def get_cloudwatch_metrics():
    """Get Bedrock metrics from CloudWatch"""
    cloudwatch = boto3.client(
        'cloudwatch',
        region_name=aws_config.bedrock_region,
        aws_access_key_id=aws_config.access_key,
        aws_secret_access_key=aws_config.secret_key
    )
    
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=1)  # Last 1 hour
    
    metrics_to_fetch = [
        'Invocations',
        'InvocationLatency',
        'InvocationClientErrors',
        'InvocationServerErrors'
    ]
    
    print("=" * 70)
    print("AWS Bedrock Metrics (Last 1 Hour)")
    print("=" * 70)
    
    for metric_name in metrics_to_fetch:
        try:
            response = cloudwatch.get_metric_statistics(
                Namespace='AWS/Bedrock',
                MetricName=metric_name,
                Dimensions=[
                    {
                        'Name': 'ModelId',
                        'Value': aws_config.bedrock_model_id
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,  # 1 hour
                Statistics=['Sum', 'Average', 'Maximum']
            )
            
            if response['Datapoints']:
                datapoint = response['Datapoints'][0]
                print(f"\n{metric_name}:")
                
                if 'Sum' in datapoint:
                    print(f"  Total: {datapoint['Sum']:.0f}")
                if 'Average' in datapoint:
                    print(f"  Average: {datapoint['Average']:.2f}")
                if 'Maximum' in datapoint:
                    print(f"  Maximum: {datapoint['Maximum']:.2f}")
            else:
                print(f"\n{metric_name}: No data")
                
        except Exception as e:
            print(f"\n{metric_name}: Error - {e}")


def get_recent_logs():
    """Get recent CloudWatch logs for Bedrock"""
    logs = boto3.client(
        'logs',
        region_name=aws_config.bedrock_region,
        aws_access_key_id=aws_config.access_key,
        aws_secret_access_key=aws_config.secret_key
    )
    
    log_group = '/aws/bedrock/modelinvocations'
    
    print("\n" + "=" * 70)
    print("Recent Bedrock Logs (Last 10 entries)")
    print("=" * 70)
    
    try:
        # Get log streams
        streams_response = logs.describe_log_streams(
            logGroupName=log_group,
            orderBy='LastEventTime',
            descending=True,
            limit=1
        )
        
        if not streams_response['logStreams']:
            print("\nNo log streams found")
            return
        
        stream_name = streams_response['logStreams'][0]['logStreamName']
        
        # Get log events
        events_response = logs.get_log_events(
            logGroupName=log_group,
            logStreamName=stream_name,
            limit=10,
            startFromHead=False
        )
        
        for event in reversed(events_response['events']):
            timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
            print(f"\n[{timestamp}]")
            print(event['message'][:200])  # First 200 chars
            
    except logs.exceptions.ResourceNotFoundException:
        print(f"\nLog group '{log_group}' not found")
        print("Logs may not be enabled or no invocations yet")
    except Exception as e:
        print(f"\nError fetching logs: {e}")


def get_cost_estimate():
    """Estimate current cost based on usage"""
    cloudwatch = boto3.client(
        'cloudwatch',
        region_name=aws_config.bedrock_region,
        aws_access_key_id=aws_config.access_key,
        aws_secret_access_key=aws_config.secret_key
    )
    
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=1)  # Last 24 hours
    
    print("\n" + "=" * 70)
    print("Cost Estimate (Last 24 Hours)")
    print("=" * 70)
    
    try:
        response = cloudwatch.get_metric_statistics(
            Namespace='AWS/Bedrock',
            MetricName='Invocations',
            Dimensions=[
                {
                    'Name': 'ModelId',
                    'Value': aws_config.bedrock_model_id
                }
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=86400,  # 24 hours
            Statistics=['Sum']
        )
        
        if response['Datapoints']:
            total_invocations = response['Datapoints'][0]['Sum']
            
            # Estimate: ~200 tokens per invocation, $0.0001 per 1K tokens
            estimated_tokens = total_invocations * 200
            estimated_cost = (estimated_tokens / 1000) * 0.0001
            
            print(f"\nTotal Invocations: {total_invocations:.0f}")
            print(f"Estimated Tokens: {estimated_tokens:.0f}")
            print(f"Estimated Cost: ${estimated_cost:.4f}")
            print("\nNote: This is an estimate. Check AWS Billing for actual cost.")
        else:
            print("\nNo invocations in the last 24 hours")
            
    except Exception as e:
        print(f"\nError estimating cost: {e}")


def main():
    """Main monitoring function"""
    print("\n🔍 AWS Bedrock Monitoring Dashboard")
    print(f"Region: {aws_config.bedrock_region}")
    print(f"Model: {aws_config.bedrock_model_id}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Get metrics
        get_cloudwatch_metrics()
        
        # Get logs
        get_recent_logs()
        
        # Get cost estimate
        get_cost_estimate()
        
        print("\n" + "=" * 70)
        print("✓ Monitoring complete")
        print("=" * 70)
        
        print("\n📊 View in AWS Console:")
        print(f"Bedrock: https://{aws_config.bedrock_region}.console.aws.amazon.com/bedrock/home")
        print(f"CloudWatch: https://{aws_config.bedrock_region}.console.aws.amazon.com/cloudwatch/home")
        print(f"Billing: https://us-east-1.console.aws.amazon.com/cost-management/home")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
