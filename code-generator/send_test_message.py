#!/usr/bin/env python3
"""
Send test messages to SQS queue for code generation tasks.
"""
import json
import os
import sys
import uuid
from datetime import datetime

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv


def send_message(sqs_client, queue_url, specification):
    """Send a code generation task to SQS."""
    message_body = {
        "task_id": f"task_{uuid.uuid4().hex[:8]}",
        "specification": specification,
        "timestamp": datetime.now().isoformat()
    }

    try:
        response = sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message_body),
            MessageAttributes={
                'TaskType': {
                    'StringValue': 'CodeGeneration',
                    'DataType': 'String'
                },
                'Priority': {
                    'StringValue': 'Normal',
                    'DataType': 'String'
                }
            }
        )

        print(f"✓ Message sent successfully!")
        print(f"  Task ID: {message_body['task_id']}")
        print(f"  Message ID: {response['MessageId']}")
        print(f"  Specification: {specification[:100]}...")
        return True

    except ClientError as e:
        print(f"✗ Failed to send message: {e}")
        return False


def main():
    """Send test messages to SQS."""
    load_dotenv()

    # Get configuration
    queue_url = os.getenv('SQS_QUEUE_URL')
    region_name = os.getenv('AWS_REGION', 'us-east-1')

    if not queue_url:
        print("Error: SQS_QUEUE_URL environment variable is required.")
        sys.exit(1)

    # Initialize SQS client
    sqs = boto3.client('sqs', region_name=region_name)

    print("\n" + "="*60)
    print("  SQS Test Message Sender")
    print("="*60)
    print(f"  Queue: {queue_url}")
    print(f"  Region: {region_name}")
    print("="*60)

    # Test specifications
    test_specs = [
        "Build simple hello world app",
        "Create a Python script that generates random passwords with configurable length and complexity",
        "Build a simple REST API with Flask that manages a todo list with CRUD operations",
        "Create a Python CLI tool that converts Markdown files to HTML",
        "Build a simple web scraper that extracts headlines from a news website"
    ]

    print("\nAvailable test specifications:")
    for i, spec in enumerate(test_specs, 1):
        print(f"  {i}. {spec}")

    print("\nOptions:")
    print("  a. Send all test messages")
    print("  1-5. Send specific test message")
    print("  c. Enter custom specification")
    print("  q. Quit")

    while True:
        choice = input("\nEnter your choice: ").strip().lower()

        if choice == 'q':
            print("Exiting...")
            break

        elif choice == 'a':
            print("\nSending all test messages...")
            for spec in test_specs:
                send_message(sqs, queue_url, spec)
                print()

        elif choice == 'c':
            spec = input("Enter your specification: ").strip()
            if spec:
                send_message(sqs, queue_url, spec)
            else:
                print("Specification cannot be empty")

        elif choice.isdigit() and 1 <= int(choice) <= len(test_specs):
            idx = int(choice) - 1
            spec = test_specs[idx]
            print(f"\nSending: {spec}")
            send_message(sqs, queue_url, spec)

        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()