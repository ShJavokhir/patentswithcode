#!/usr/bin/env python3
"""
SQS Message Processor with Simple E2B Integration.
Polls SQS queue and processes code generation tasks using E2B sandbox and Claude.
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

from e2b_simple import SimpleE2BGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SQSSimpleProcessor:
    """Processes SQS messages for code generation using E2B sandbox."""

    def __init__(self, queue_url: str, region_name: Optional[str] = None):
        """
        Initialize the SQS processor.

        Args:
            queue_url: The URL of the SQS queue
            region_name: AWS region name (optional)
        """
        self.queue_url = queue_url
        self.sqs = boto3.client('sqs', region_name=region_name)
        self.generator = SimpleE2BGenerator()
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
                    MessageAttributeNames=['All'],
                    VisibilityTimeout=180  # 3 minutes to process
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

                        # Save result
                        self._save_result(result)

                        # Delete message from queue after successful processing
                        if result.get('status') == 'completed':
                            self._delete_message(message['ReceiptHandle'])
                            logger.info("✅ Task completed successfully")
                        else:
                            logger.warning(f"⚠️ Task failed: {result.get('error', 'Unknown error')}")

                    except Exception as e:
                        logger.error(f"Failed to process message {message.get('MessageId')}: {e}")

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
        Process a single SQS message.

        Args:
            message: The SQS message dictionary

        Returns:
            Processing result dictionary
        """
        logger.info(f"Processing message ID: {message.get('MessageId')}")

        body = message.get('Body', '')

        try:
            # Parse the message
            task_data = json.loads(body)
        except json.JSONDecodeError:
            task_data = {"specification": body}

        # Process with E2B generator
        result = self.generator.process_task(task_data)

        # Add message metadata
        result['message_id'] = message.get('MessageId')

        return result

    def _save_result(self, result: Dict[str, Any]):
        """
        Save the processing result metadata.

        Args:
            result: The processing result dictionary
        """
        # Create results directory if it doesn't exist
        results_dir = 'results'
        os.makedirs(results_dir, exist_ok=True)

        # Generate filename for metadata
        task_id = result.get('task_id', result.get('message_id', 'unknown'))
        timestamp = int(time.time())
        filename = f"{results_dir}/{task_id}_{timestamp}_metadata.json"

        # Save metadata (without large code content)
        metadata = {
            'task_id': result.get('task_id'),
            'status': result.get('status'),
            'specification': result.get('specification'),
            's3_url': result.get('s3_url'),
            'files_created': result.get('files_created', []),
            'timestamp': result.get('timestamp'),
            'message_id': result.get('message_id')
        }

        with open(filename, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"📁 Metadata saved to {filename}")

        # Log summary
        if result.get('status') == 'completed':
            if result.get('files_created'):
                logger.info(f"  📄 Files created: {len(result['files_created'])} files")
            if result.get('s3_url'):
                logger.info(f"  ☁️ Archive uploaded to S3: {result.get('s3_url')}")

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
    """Main entry point for the SQS processor."""
    # Load environment variables
    load_dotenv()

    # Get configuration
    queue_url = os.getenv('SQS_QUEUE_URL')
    region_name = os.getenv('AWS_REGION', 'us-east-1')
    max_messages = int(os.getenv('MAX_MESSAGES', '1'))
    wait_time = int(os.getenv('WAIT_TIME_SECONDS', '20'))

    # Validate required environment variables
    required_vars = ['SQS_QUEUE_URL', 'E2B_API_KEY', 'ANTHROPIC_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set them in your .env file")
        sys.exit(1)

    print("\n" + "="*60)
    print("  SQS E2B Code Generator")
    print("="*60)
    print(f"  Region: {region_name}")
    print(f"  Queue: {queue_url}")
    print("  Using: E2B Sandbox + Claude API")
    print("="*60 + "\n")

    try:
        processor = SQSSimpleProcessor(queue_url=queue_url, region_name=region_name)
        processor.poll_and_process(max_messages=max_messages, wait_time=wait_time)
    except Exception as e:
        logger.error(f"Failed to start processor: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()