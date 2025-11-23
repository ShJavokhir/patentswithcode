#!/usr/bin/env python3
"""
SQS Message Processor with E2B Sandbox Integration.
Polls SQS queue and processes code generation tasks using E2B sandbox.
"""
import json
import os
import sys
import time
import logging
from typing import Optional, Dict, Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from dotenv import load_dotenv

from e2b_handler import process_sqs_message

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SQSE2BProcessor:
    """Processes SQS messages for code generation tasks using E2B sandbox."""

    def __init__(self, queue_url: str, region_name: Optional[str] = None):
        """
        Initialize the SQS E2B processor.

        Args:
            queue_url: The URL of the SQS queue
            region_name: AWS region name (optional, uses default if not provided)
        """
        self.queue_url = queue_url
        self.sqs = boto3.client('sqs', region_name=region_name)
        self.running = True

    def poll_and_process(self, max_messages: int = 1, wait_time: int = 20):
        """
        Poll messages from SQS and process them with E2B.

        Args:
            max_messages: Maximum number of messages to retrieve per request (1-10)
            wait_time: Long polling wait time in seconds (0-20)
        """
        logger.info(f"Starting SQS E2B processor for queue: {self.queue_url}")
        logger.info(f"Max messages per request: {max_messages}, Wait time: {wait_time}s")
        print("-" * 80)

        while self.running:
            try:
                # Receive messages from SQS
                response = self.sqs.receive_message(
                    QueueUrl=self.queue_url,
                    MaxNumberOfMessages=max_messages,
                    WaitTimeSeconds=wait_time,
                    AttributeNames=['All'],
                    MessageAttributeNames=['All']
                )

                messages = response.get('Messages', [])

                if not messages:
                    logger.info("No messages received, continuing to poll...")
                    continue

                logger.info(f"Received {len(messages)} message(s)")

                for message in messages:
                    try:
                        # Process the message
                        result = self._process_message(message)

                        # Save result to file (or send to another queue/database)
                        self._save_result(result)

                        # Delete message from queue after successful processing
                        self._delete_message(message['ReceiptHandle'])

                    except Exception as e:
                        logger.error(f"Failed to process message {message.get('MessageId')}: {e}")
                        # Don't delete the message on failure - let it retry

            except ClientError as e:
                error_code = e.response['Error']['Code']
                error_message = e.response['Error']['Message']
                logger.error(f"AWS Client Error ({error_code}): {error_message}")
                time.sleep(5)
            except BotoCoreError as e:
                logger.error(f"BotoCore Error: {str(e)}")
                time.sleep(5)
            except KeyboardInterrupt:
                logger.info("Received interrupt signal, shutting down gracefully...")
                self.running = False
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                time.sleep(5)

        logger.info("Stopped polling messages.")

    def _process_message(self, message: dict) -> Dict[str, Any]:
        """
        Process a single SQS message with E2B handler.

        Args:
            message: The SQS message dictionary

        Returns:
            Processing result dictionary
        """
        logger.info(f"Processing message ID: {message.get('MessageId')}")

        body = message.get('Body', '')

        # Process with E2B handler
        result = process_sqs_message(body)

        # Add message metadata to result
        result['message_id'] = message.get('MessageId')
        result['receipt_handle'] = message.get('ReceiptHandle')

        return result

    def _save_result(self, result: Dict[str, Any]):
        """
        Save the processing result to a file.

        Args:
            result: The processing result dictionary
        """
        # Create results directory if it doesn't exist
        results_dir = 'results'
        os.makedirs(results_dir, exist_ok=True)

        # Generate filename based on task ID or message ID
        task_id = result.get('task_id', result.get('message_id', 'unknown'))
        filename = f"{results_dir}/{task_id}_{int(time.time())}.json"

        # Save result to file
        with open(filename, 'w') as f:
            json.dump(result, f, indent=2)

        logger.info(f"Result saved to {filename}")

        # Log summary
        if result.get('status') == 'completed':
            logger.info(f"✓ Task completed successfully")
            if result.get('files_created'):
                logger.info(f"  Files created: {result['files_created']}")
        else:
            logger.error(f"✗ Task failed: {result.get('error', 'Unknown error')}")

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
            logger.info("Message deleted from queue successfully.")
        except ClientError as e:
            logger.error(f"Failed to delete message: {e}")


def main():
    """Main entry point for the SQS E2B processor."""
    # Load environment variables from .env file
    load_dotenv()

    # Get configuration from environment variables
    queue_url = os.getenv('SQS_QUEUE_URL')
    region_name = os.getenv('AWS_REGION', 'us-east-1')
    max_messages = int(os.getenv('MAX_MESSAGES', '1'))  # Process one at a time for E2B
    wait_time = int(os.getenv('WAIT_TIME_SECONDS', '20'))

    # Validate required environment variables
    required_vars = ['SQS_QUEUE_URL', 'E2B_API_KEY', 'ANTHROPIC_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set them in your .env file")
        sys.exit(1)

    print("\n" + "="*60)
    print("  SQS E2B Code Generation Processor")
    print("="*60)
    print(f"  Region: {region_name}")
    print(f"  Queue: {queue_url}")
    print("="*60 + "\n")

    try:
        processor = SQSE2BProcessor(queue_url=queue_url, region_name=region_name)
        processor.poll_and_process(max_messages=max_messages, wait_time=wait_time)
    except Exception as e:
        logger.error(f"Failed to start processor: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()