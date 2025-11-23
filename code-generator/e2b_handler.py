#!/usr/bin/env python3
"""
E2B Sandbox handler for code generation tasks.
Receives specifications via SQS and uses E2B sandbox with Claude to generate code.
"""
import json
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from e2b_code_interpreter import Sandbox
from anthropic import Anthropic
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class E2BCodeGenerator:
    """Handles code generation using E2B sandbox and Claude API."""

    def __init__(self):
        """Initialize the E2B and Claude clients."""
        load_dotenv()

        # Initialize Anthropic client
        self.anthropic = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

        # Set E2B API key as environment variable (required by E2B SDK)
        self.e2b_api_key = os.getenv('E2B_API_KEY')
        if self.e2b_api_key:
            os.environ['E2B_API_KEY'] = self.e2b_api_key
        else:
            raise ValueError("E2B_API_KEY is required")

        if not os.getenv('ANTHROPIC_API_KEY'):
            raise ValueError("ANTHROPIC_API_KEY is required")

    def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a code generation task in E2B sandbox.

        Args:
            task_data: Dictionary containing the task specification

        Returns:
            Result dictionary with generated code and metadata
        """
        specification = task_data.get('specification', '')
        task_id = task_data.get('task_id', f"task_{datetime.now().timestamp()}")

        logger.info(f"Processing task {task_id}: {specification[:100]}...")

        sandbox = None
        try:
            # Create E2B sandbox
            sandbox = self._create_sandbox()

            # Generate implementation plan with Claude
            implementation_plan = self._generate_plan(specification)

            # Execute code generation in sandbox
            result = self._execute_in_sandbox(sandbox, specification, implementation_plan)

            return {
                'task_id': task_id,
                'status': 'completed',
                'specification': specification,
                'implementation_plan': implementation_plan,
                'generated_code': result.get('code'),
                'files_created': result.get('files'),
                'execution_logs': result.get('logs'),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error processing task {task_id}: {str(e)}")
            return {
                'task_id': task_id,
                'status': 'failed',
                'error': str(e),
                'specification': specification,
                'timestamp': datetime.now().isoformat()
            }
        finally:
            # Always close the sandbox if it was created
            if sandbox:
                try:
                    sandbox.close()
                    logger.info("Sandbox closed successfully")
                except Exception as e:
                    logger.warning(f"Error closing sandbox: {e}")

    def _create_sandbox(self) -> Sandbox:
        """Create and initialize E2B sandbox."""
        logger.info("Creating E2B sandbox...")

        # Create sandbox with Python environment (E2B SDK reads API key from environment)
        sandbox = Sandbox()

        # Test sandbox is working
        result = sandbox.run_code("""
import sys
print(f"Python {sys.version}")
print("Sandbox initialized successfully")
        """)

        if result.error:
            logger.error(f"Sandbox initialization error: {result.error}")
        else:
            logger.info(f"Sandbox initialized: {result.text}")

        return sandbox

    def _generate_plan(self, specification: str) -> str:
        """
        Use Claude to generate an implementation plan.

        Args:
            specification: The user's code generation request

        Returns:
            Implementation plan as a string
        """
        logger.info("Generating implementation plan with Claude...")

        prompt = f"""You are an expert software architect. Given the following specification,
        create a detailed implementation plan for building this application.

        Specification: {specification}

        Provide a structured plan including:
        1. Project structure
        2. Key files to create
        3. Main components/functions
        4. Dependencies needed

        Keep it simple and practical. Focus on a minimal working implementation.
        """

        response = self.anthropic.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return response.content[0].text

    def _execute_in_sandbox(self, sandbox: Sandbox, specification: str, plan: str) -> Dict[str, Any]:
        """
        Execute the code generation in the E2B sandbox.

        Args:
            sandbox: E2B sandbox instance
            specification: Original specification
            plan: Implementation plan

        Returns:
            Dictionary with generated code and execution results
        """
        logger.info("Executing code generation in sandbox...")

        # Generate the actual code using Claude
        code_prompt = f"""Based on this specification and implementation plan,
        generate the complete working code.

        Specification: {specification}

        Plan: {plan}

        Generate Python code that creates all necessary files for a working application.
        Use file operations to create the project structure and files.
        Make sure to create a main entry point file.

        Return executable Python code that will create the entire application.
        """

        response = self.anthropic.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            messages=[
                {"role": "user", "content": code_prompt}
            ]
        )

        generated_code = response.content[0].text

        # Extract Python code blocks if wrapped in markdown
        if "```python" in generated_code:
            import re
            code_blocks = re.findall(r'```python\n(.*?)\n```', generated_code, re.DOTALL)
            if code_blocks:
                generated_code = '\n\n'.join(code_blocks)

        # Execute the code in sandbox
        logger.info("Running generated code in sandbox...")
        execution_result = sandbox.run_code(generated_code)

        # List created files
        list_files_code = """
import os
import json

def list_all_files(directory='.'):
    files = []
    for root, dirs, filenames in os.walk(directory):
        # Skip hidden and system directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        for filename in filenames:
            if not filename.startswith('.') and not filename.endswith('.pyc'):
                filepath = os.path.join(root, filename)
                # Only include if it's a file we likely created
                if os.path.isfile(filepath) and os.path.getsize(filepath) > 0:
                    files.append(filepath)
    return files

created_files = list_all_files()
if created_files:
    print(json.dumps(created_files))
else:
    print('[]')
        """

        files_result = sandbox.run_code(list_files_code)

        created_files = []
        if files_result.text:
            try:
                text = files_result.text.strip()
                if text and text != 'None':
                    created_files = json.loads(text)
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Could not parse file list: {e}")
                created_files = []

        # Read the main file content if it exists
        main_file_content = ""
        if created_files:
            # Try to find main.py or app.py
            for main_candidate in ['main.py', 'app.py', 'hello.py']:
                if any(main_candidate in f for f in created_files):
                    read_code = f"""
with open('{main_candidate}', 'r') as f:
    print(f.read())
                    """
                    content_result = sandbox.run_code(read_code)
                    if content_result.text:
                        main_file_content = content_result.text
                        break

        return {
            'code': generated_code,
            'files': created_files,
            'main_file_content': main_file_content,
            'logs': {
                'execution_output': execution_result.text if execution_result.text else '',
                'execution_error': execution_result.error if execution_result.error else ''
            }
        }


def process_sqs_message(message_body: str) -> Dict[str, Any]:
    """
    Process an SQS message containing a code generation task.

    Args:
        message_body: JSON string with task specification

    Returns:
        Processing result dictionary
    """
    try:
        # Parse the message
        task_data = json.loads(message_body)

        # Initialize the code generator
        generator = E2BCodeGenerator()

        # Process the task
        result = generator.process_task(task_data)

        return result

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in message: {e}")
        return {
            'status': 'failed',
            'error': f'Invalid JSON: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {
            'status': 'failed',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


if __name__ == "__main__":
    # Test with a simple example
    test_task = {
        "specification": "Build a simple hello world Flask web application with a home route that returns 'Hello, World!'"
    }

    result = process_sqs_message(json.dumps(test_task))
    print("\nTask Result:")
    print(json.dumps(result, indent=2))