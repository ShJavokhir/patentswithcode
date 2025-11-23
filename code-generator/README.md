# E2B Code Generator with SQS Integration

A Python-based system that receives code generation tasks via AWS SQS and uses Claude Code CLI running inside E2B sandboxes to generate complete applications.

## Architecture

The system consists of:

1. **SQS Queue** - Receives code generation task specifications
2. **E2B Sandbox** - Isolated environment where Claude Code CLI runs
3. **Claude Code CLI** - Anthropic's official code generation tool running inside the sandbox
4. **SQS Processor** - Polls queue and orchestrates the code generation

## Components

### Core Files (Working Implementation)

- `sqs_processor_simple.py` - Main SQS processor that polls queue and processes messages
- `e2b_simple.py` - Simple, robust E2B integration with Claude API
- `send_test_message.py` - Send test messages to SQS queue

### Alternative/Experimental Files

- `e2b_claude_handler.py` - Attempt to use Claude Code CLI (not yet available on npm)
- `e2b_handler.py` - Earlier implementation attempt
- `e2b_claude_sync.py` - Synchronous version for testing

### Utility Files

- `sqs_reader.py` - Simple SQS reader for debugging
- `send_test_message.py` - Send test messages to SQS queue

## Setup

### 1. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Required environment variables:
- `AWS_REGION` - AWS region for SQS
- `AWS_ACCESS_KEY_ID` - AWS access key
- `AWS_SECRET_ACCESS_KEY` - AWS secret key
- `SQS_QUEUE_URL` - Full URL of your SQS queue
- `E2B_API_KEY` - E2B API key (get from https://e2b.dev)
- `ANTHROPIC_API_KEY` - Claude API key (get from https://console.anthropic.com)

## Usage

### Running the Main Processor

Start the SQS processor to handle code generation tasks:

```bash
python sqs_processor_simple.py
```

This will:
1. Poll the SQS queue for messages
2. Use Claude API to generate code
3. Create an E2B sandbox and execute the code
4. Save results to the `results/` directory

### Testing Locally (Without SQS)

Test the E2B handler directly:

```bash
python e2b_simple.py
```

This runs several test scenarios:
- Simple Hello World application
- Flask web application
- Calculator module

### Sending Test Messages to SQS

Send test tasks to your SQS queue:

```bash
python send_test_message.py
```

This provides an interactive menu to:
- Send predefined test specifications
- Send custom specifications
- Send multiple messages at once

## Message Format

SQS messages should be JSON with the following structure:

```json
{
  "specification": "Build simple hello world app"
}
```

Optional fields:
- `task_id` - Unique identifier for the task (auto-generated if not provided)

## How It Works

1. **Message Reception**: SQS processor receives a message with a code specification
2. **Code Generation**: Claude API generates complete Python code based on the specification
3. **Sandbox Creation**: E2B sandbox is created for secure code execution
4. **Code Execution**: Generated code runs in the sandbox to create application files
5. **File Collection**: The system lists all created files in the sandbox
6. **Result Storage**: Generated files and execution logs are saved to the results directory

## Example Specifications

Simple examples you can use:

- "Build simple hello world app"
- "Create a Python calculator with basic operations"
- "Build a Flask REST API for managing todos"
- "Create a password generator CLI tool"
- "Build a simple web scraper for news headlines"

## Output

Results are saved in the `results/` directory as JSON files containing:
- Task ID and status
- Original specification
- Implementation plan
- Generated code
- List of created files
- Execution logs

## Error Handling

The system handles:
- Invalid JSON in messages
- E2B sandbox failures
- Claude API errors
- SQS connection issues

Failed messages remain in the queue for retry according to your SQS configuration.

## Development

### Running Tests

```bash
# Test E2B handler locally
python test_e2b_local.py

# Test SQS connectivity
python sqs_reader.py
```

### Debugging

- Check `results/` directory for processing outputs
- Monitor console logs for real-time processing information
- Use `sqs_reader.py` to inspect raw queue messages

## Security Notes

- Keep your `.env` file secure and never commit it
- Use IAM roles with minimal permissions for production
- Consider implementing message encryption for sensitive specifications
- Monitor E2B sandbox usage and costs

## Limitations

- Processes one message at a time to avoid E2B rate limits
- Generated code is limited to Python applications
- Sandbox execution timeout is set to 5 minutes

## Future Improvements

- Support for multiple programming languages
- Parallel processing with multiple E2B sandboxes
- Integration with version control systems
- Web interface for monitoring and management
- Support for more complex multi-file projects