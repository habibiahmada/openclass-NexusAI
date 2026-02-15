#!/bin/bash
# AWS deployment script for OpenClass Nexus AI

echo "Deploying OpenClass Nexus AI to AWS..."

# Check AWS CLI
aws --version || { echo "AWS CLI required"; exit 1; }

# Create EC2 instance
aws ec2 run-instances \
    --image-id ami-0c02fb55956c7d316 \
    --instance-type t3.medium \
    --key-name openclass-key \
    --security-group-ids sg-xxxxxxxxx \
    --user-data file://user-data.sh \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=OpenClass-Nexus-AI}]'

echo "AWS deployment initiated!"
