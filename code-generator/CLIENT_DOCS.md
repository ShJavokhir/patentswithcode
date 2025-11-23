# SQS Message Format for Code Generation

## Quick Reference

Send JSON messages to the SQS queue to generate code automatically.

**Queue URL:** `https://sqs.us-east-1.amazonaws.com/390403864981/hackathon.fifo`

## Message Format

### Basic Structure
```json
{
  "specification": "Your code generation request here"
}
```

### With Optional Task ID
```json
{
  "task_id": "unique-task-id",
  "specification": "Build a Flask REST API for todo management"
}
```

## Example Requests

### Simple Applications
```json
{"specification": "Build a simple hello world Python script"}
{"specification": "Create a calculator with add, subtract, multiply, divide"}
{"specification": "Build a password generator with configurable options"}
```

### Web Applications
```json
{"specification": "Create a Flask REST API with CRUD operations for todos"}
{"specification": "Build a simple web scraper for news headlines"}
{"specification": "Create an HTML form with validation"}
```

## Sending Messages

### AWS CLI
```bash
aws sqs send-message \
  --queue-url https://sqs.us-east-1.amazonaws.com/390403864981/hackathon.fifo \
  --message-body '{"specification":"Build a hello world app"}' \
  --message-group-id "default" \
  --message-deduplication-id "$(date +%s)"
```

### Python (Boto3)
```python
import boto3
import json
import time

sqs = boto3.client('sqs', region_name='us-east-1')

message = {
    "specification": "Create a Python calculator module"
}

response = sqs.send_message(
    QueueUrl='https://sqs.us-east-1.amazonaws.com/390403864981/hackathon.fifo',
    MessageBody=json.dumps(message),
    MessageGroupId='default',
    MessageDeduplicationId=str(time.time())
)

print(f"Message sent: {response['MessageId']}")
```

### cURL
```bash
# Note: Requires AWS signature - use AWS CLI or SDK instead
```

## Response

The system will:
1. Generate complete code based on your specification
2. Execute it in a secure E2B sandbox
3. Create an archive of all generated files
4. Store locally in `archives/` directory
5. Optionally upload to S3 (if permissions available)

## Output Structure

Generated archives contain:
- All source code files
- Configuration files
- README/documentation (if requested)
- Dependencies list (if applicable)

## Tips

- Be specific in your specifications
- Include technology preferences (e.g., "using Flask" or "in Python")
- Mention if you need specific files (README, requirements.txt, etc.)
- Processing typically takes 10-30 seconds

## Limitations

- Primarily generates Python applications
- Maximum specification length: ~1000 characters
- Files are archived as `.tar.gz`
- FIFO queue requires MessageGroupId and MessageDeduplicationId