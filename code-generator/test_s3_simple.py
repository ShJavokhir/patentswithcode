#!/usr/bin/env python3
"""
Simple test to verify S3 functionality.
"""
import os
import sys
from dotenv import load_dotenv
import boto3
from botocore.exceptions import ClientError

# Load environment variables
load_dotenv()

# Test S3 configuration
s3_bucket = os.getenv('S3_BUCKET', 'code-generation-results')
region = os.getenv('AWS_REGION', 'us-east-1')

print(f"Testing S3 Configuration:")
print(f"  Bucket: {s3_bucket}")
print(f"  Region: {region}")

# Create S3 client
try:
    s3_client = boto3.client('s3', region_name=region)

    # Test creating bucket if it doesn't exist
    try:
        s3_client.head_bucket(Bucket=s3_bucket)
        print(f"✅ Bucket '{s3_bucket}' exists and is accessible")
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            print(f"⚠️ Bucket '{s3_bucket}' does not exist. Creating...")
            try:
                if region == 'us-east-1':
                    s3_client.create_bucket(Bucket=s3_bucket)
                else:
                    s3_client.create_bucket(
                        Bucket=s3_bucket,
                        CreateBucketConfiguration={'LocationConstraint': region}
                    )
                print(f"✅ Created bucket '{s3_bucket}'")
            except ClientError as create_error:
                print(f"❌ Failed to create bucket: {create_error}")
                sys.exit(1)
        else:
            print(f"❌ Error accessing bucket: {e}")
            sys.exit(1)

    # Test uploading a simple file
    test_content = "Test file for S3 upload verification"
    test_key = "test/test-upload.txt"

    try:
        s3_client.put_object(
            Bucket=s3_bucket,
            Key=test_key,
            Body=test_content.encode('utf-8'),
            ContentType='text/plain'
        )
        print(f"✅ Successfully uploaded test file to s3://{s3_bucket}/{test_key}")

        # Clean up test file
        s3_client.delete_object(Bucket=s3_bucket, Key=test_key)
        print(f"✅ Cleaned up test file")

    except ClientError as e:
        print(f"❌ Failed to upload test file: {e}")
        sys.exit(1)

    print("\n🎉 S3 configuration is working correctly!")

except Exception as e:
    print(f"❌ S3 client initialization failed: {e}")
    print("\nPlease check your AWS credentials and configuration.")
    sys.exit(1)