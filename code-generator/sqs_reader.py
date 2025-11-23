#!/usr/bin/env python3
"""
Simple and robust SQS event reader that polls messages and prints them.
"""
import json
import os
import sys
import time
from typing import Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from dotenv import load_dotenv


class SQSReader:
    """Reads and processes messages from an AWS SQS queue."""

    def __init__(self, queue_url: str, region_name: Optional[str] = None):
        """
        Initialize the SQS reader.

        Args:
            queue_url: The URL of the SQS queue
            region_name: AWS region name (optional, uses default if not provided)
        """
        self.queue_url = queue_url
        self.sqs = boto3.client('sqs', region_name=region_name)
        self.running = True

    def poll_messages(self, max_messages: int = 10, wait_time: int = 20):
        """
        Poll messages from the SQS queue and print them.

        Args:
            max_messages: Maximum number of messages to retrieve per request (1-10)
            wait_time: Long polling wait time in seconds (0-20)
        """
        print(f"Starting to poll messages from queue: {self.queue_url}")
        print(f"Max messages per request: {max_messages}, Wait time: {wait_time}s")
        print("-" * 80)

        while self.running:
            try:
                response = self.sqs.receive_message(
                    QueueUrl=self.queue_url,
                    MaxNumberOfMessages=max_messages,
                    WaitTimeSeconds=wait_time,
                    AttributeNames=['All'],
                    MessageAttributeNames=['All']
                )

                messages = response.get('Messages', [])

                if not messages:
                    print("No messages received, continuing to poll...")
                    continue

                print(f"\nReceived {len(messages)} message(s)")

                for message in messages:
                    self._process_message(message)
                    self._delete_message(message['ReceiptHandle'])

            except ClientError as e:
                error_code = e.response['Error']['Code']
                error_message = e.response['Error']['Message']
                print(f"AWS Client Error ({error_code}): {error_message}", file=sys.stderr)
                time.sleep(5)
            except BotoCoreError as e:
                print(f"BotoCore Error: {str(e)}", file=sys.stderr)
                time.sleep(5)
            except KeyboardInterrupt:
                print("\n\nReceived interrupt signal, shutting down gracefully...")
                self.running = False
            except Exception as e:
                print(f"Unexpected error: {str(e)}", file=sys.stderr)
                time.sleep(5)

        print("Stopped polling messages.")

    def _process_message(self, message: dict):
        """
        Process and print a single message.

        Args:
            message: The SQS message dictionary
        """
        print("\n" + "=" * 80)
        print(f"Message ID: {message.get('MessageId')}")
        print(f"Receipt Handle: {message.get('ReceiptHandle')[:50]}...")

        body = message.get('Body', '')

        # Try to parse as JSON for pretty printing
        try:
            body_json = json.loads(body)
            print("Message Body (JSON):")
            print(json.dumps(body_json, indent=2))
        except json.JSONDecodeError:
            print("Message Body (Text):")
            print(body)

        # Print message attributes if present
        if message.get('MessageAttributes'):
            print("\nMessage Attributes:")
            for key, value in message['MessageAttributes'].items():
                print(f"  {key}: {value.get('StringValue', value.get('BinaryValue', 'N/A'))}")

        # Print system attributes if present
        if message.get('Attributes'):
            print("\nSystem Attributes:")
            for key, value in message['Attributes'].items():
                print(f"  {key}: {value}")

        print("=" * 80)

    def _delete_message(self, receipt_handle: str):
        """
        Delete a message from the queue after processing.

        Args:
            receipt_handle: The receipt handle of the message to delete
        """
        try:
            self.sqs.delete_message(
                QueueUrl=self.queue_url,
                ReceiptHandle=receipt_handle
            )
            print("Message deleted successfully.")
        except ClientError as e:
            print(f"Failed to delete message: {e}", file=sys.stderr)


def main():
    """Main entry point for the SQS reader."""
    # Load environment variables from .env file
    load_dotenv()

    # Get configuration from environment variables
    queue_url = os.getenv('SQS_QUEUE_URL')
    region_name = os.getenv('AWS_REGION', 'us-east-1')
    max_messages = int(os.getenv('MAX_MESSAGES', '10'))
    wait_time = int(os.getenv('WAIT_TIME_SECONDS', '20'))

    if not queue_url:
        print("Error: SQS_QUEUE_URL environment variable is required.", file=sys.stderr)
        print("Please set it in your .env file or export it in your shell.")
        sys.exit(1)

    print("SQS Event Reader")
    print(f"Region: {region_name}")
    print()

    try:
        reader = SQSReader(queue_url=queue_url, region_name=region_name)
        reader.poll_messages(max_messages=max_messages, wait_time=wait_time)
    except Exception as e:
        print(f"Failed to start SQS reader: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
