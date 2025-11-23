#!/usr/bin/env python3
"""
E2B Sandbox handler that runs Claude Code inside the sandbox for code generation.
This approach uses Claude Code CLI directly in the sandbox for more robust execution.
"""
import json
import os
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from e2b import Sandbox
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class E2BClaudeCodeGenerator:
    """Handles code generation using Claude Code inside E2B sandbox."""

    def __init__(self):
        """Initialize the E2B configuration."""
        load_dotenv()

        # Set E2B API key as environment variable (required by E2B SDK)
        self.e2b_api_key = os.getenv('E2B_API_KEY')
        if self.e2b_api_key:
            os.environ['E2B_API_KEY'] = self.e2b_api_key
        else:
            raise ValueError("E2B_API_KEY is required")

        # Get Anthropic API key for Claude Code
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        if not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required")

        # Template name - you can create a custom template or use default
        self.template = os.getenv('E2B_TEMPLATE', 'base')

    async def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a code generation task using Claude Code in E2B sandbox.

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
            # Create E2B sandbox with Anthropic API key
            sandbox = await self._create_sandbox()

            # Execute Claude Code in the sandbox
            result = await self._execute_claude_code(sandbox, specification)

            # List created files
            files = await self._list_created_files(sandbox)

            # Get the main file content if exists
            main_content = await self._get_main_file_content(sandbox, files)

            return {
                'task_id': task_id,
                'status': 'completed',
                'specification': specification,
                'files_created': files,
                'main_file_content': main_content,
                'execution_output': result.get('output', ''),
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
                    await sandbox.kill()
                    logger.info("Sandbox terminated successfully")
                except Exception as e:
                    logger.warning(f"Error terminating sandbox: {e}")

    async def _create_sandbox(self) -> Sandbox:
        """Create and initialize E2B sandbox with Claude Code installed."""
        logger.info("Creating E2B sandbox...")

        # Create sandbox - simpler approach
        sandbox = await Sandbox.create(
            template=self.template,
            timeout=300  # 5 minutes timeout
        )

        logger.info(f"Sandbox created with ID: {sandbox.id}")

        # Set environment variable for Anthropic API key
        logger.info("Setting up environment variables...")
        await sandbox.commands.run(
            f"export ANTHROPIC_API_KEY='{self.anthropic_api_key}'",
            timeout=5
        )

        # Install Claude Code if not already in the template
        logger.info("Setting up Claude Code in sandbox...")

        # First, check if Node.js is available
        node_check = await sandbox.commands.run("node --version")
        if node_check.exit_code != 0:
            logger.info("Installing Node.js...")
            install_node = await sandbox.commands.run(
                "curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && apt-get install -y nodejs",
                timeout=60
            )
            if install_node.exit_code != 0:
                raise Exception(f"Failed to install Node.js: {install_node.stderr}")

        # Install Claude Code globally
        logger.info("Installing Claude Code CLI...")
        install_result = await sandbox.commands.run(
            "npm install -g @anthropics/claude-code",
            timeout=120
        )

        if install_result.exit_code != 0:
            logger.warning(f"Claude Code installation warning: {install_result.stderr}")
            # Try alternative installation method
            alt_install = await sandbox.commands.run(
                "npx -y @anthropics/claude-code --version",
                timeout=30
            )
            if alt_install.exit_code != 0:
                raise Exception(f"Failed to install Claude Code: {install_result.stderr}")

        # Verify Claude Code is available
        verify = await sandbox.commands.run("claude --version || npx -y @anthropics/claude-code --version")
        logger.info(f"Claude Code version: {verify.stdout}")

        return sandbox

    async def _execute_claude_code(self, sandbox: Sandbox, specification: str) -> Dict[str, Any]:
        """
        Execute Claude Code in the sandbox to generate the application.

        Args:
            sandbox: E2B sandbox instance
            specification: The code generation specification

        Returns:
            Dictionary with execution results
        """
        logger.info("Executing Claude Code for code generation...")

        # Prepare the prompt for Claude Code
        prompt = f"""Create a complete working application based on this specification:

{specification}

You are a coding agent that converts technical specifications into working code.

**Default Stack** (unless specs specify otherwise):
- TypeScript + React (hooks)
- Tailwind CSS for styling
- Single-file component when possible
- No external APIs or backends

**Implementation Rules**:
1. Read the entire spec carefully before coding
2. Create self-contained, immediately runnable components
3. Generate realistic mock data matching spec data structures
4. Implement ALL described interactions and UI elements exactly as specified
5. Follow visual specifications precisely (colors, dimensions, animations, timing)
6. Meet all success criteria listed in specs
7. Respect exclusions - don't implement explicitly excluded features
8. Use appropriate state management for complexity level

**Output**:
- Complete, production-ready code
- Proper TypeScript types for all data structures
- Brief setup notes only if non-standard dependencies needed
- No explanations - just working code

**Constraints**:
- Frontend-only implementation
- Must work immediately when imported/rendered
- No placeholder functions - everything must be functional

Your goal: Produce a working demonstration of the described system that can be tested immediately.

Please implement this now. You need to create JSX files."""

        # Execute Claude Code with the prompt
        # Set ANTHROPIC_API_KEY inline and use npx if claude command is not available globally
        command = f'''export ANTHROPIC_API_KEY='{self.anthropic_api_key}' && echo "{prompt}" | (claude -p --dangerously-skip-permissions 2>/dev/null || npx -y @anthropics/claude-code -p --dangerously-skip-permissions)'''

        logger.info("Running Claude Code command...")
        result = await sandbox.commands.run(
            command,
            timeout=180,  # 3 minutes for code generation
            shell=True
        )

        if result.exit_code != 0:
            logger.error(f"Claude Code execution failed: {result.stderr}")
            # Try without flags if it fails
            simple_command = f'''export ANTHROPIC_API_KEY='{self.anthropic_api_key}' && echo "{prompt}" | (claude 2>/dev/null || npx -y @anthropics/claude-code)'''
            result = await sandbox.commands.run(
                simple_command,
                timeout=180,
                shell=True
            )

        logger.info(f"Claude Code execution completed with exit code: {result.exit_code}")

        return {
            'output': result.stdout,
            'error': result.stderr,
            'exit_code': result.exit_code
        }

    async def _list_created_files(self, sandbox: Sandbox) -> list:
        """
        List all files created in the sandbox.

        Args:
            sandbox: E2B sandbox instance

        Returns:
            List of file paths
        """
        logger.info("Listing created files...")

        # Find all files created (excluding system files)
        command = """find . -type f -name "*.py" -o -name "*.js" -o -name "*.html" -o -name "*.css" -o -name "*.json" -o -name "*.md" -o -name "*.txt" 2>/dev/null | grep -v node_modules | grep -v ".git" | head -20"""

        result = await sandbox.commands.run(command)

        files = []
        if result.stdout:
            files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
            logger.info(f"Found {len(files)} files")

        return files

    async def _get_main_file_content(self, sandbox: Sandbox, files: list) -> str:
        """
        Get the content of the main file if it exists.

        Args:
            sandbox: E2B sandbox instance
            files: List of created files

        Returns:
            Content of the main file
        """
        # Look for common main file names
        main_candidates = ['main.py', './main.py', 'app.py', './app.py',
                          'index.js', './index.js', 'index.html', './index.html']

        for candidate in main_candidates:
            if any(candidate in f or f.endswith(candidate.lstrip('./')) for f in files):
                result = await sandbox.commands.run(f"cat {candidate} 2>/dev/null")
                if result.exit_code == 0 and result.stdout:
                    logger.info(f"Found main file: {candidate}")
                    return result.stdout

        # If no standard main file, return the first Python or JavaScript file
        for file in files:
            if file.endswith(('.py', '.js')):
                result = await sandbox.commands.run(f"cat {file}")
                if result.exit_code == 0:
                    logger.info(f"Returning content of: {file}")
                    return result.stdout

        return ""


def process_sqs_message_sync(message_body: str) -> Dict[str, Any]:
    """
    Synchronous wrapper for processing SQS messages.

    Args:
        message_body: JSON string with task specification

    Returns:
        Processing result dictionary
    """
    try:
        # Parse the message
        task_data = json.loads(message_body)

        # Run the async function
        return asyncio.run(process_sqs_message_async(task_data))

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


async def process_sqs_message_async(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Async function to process an SQS message containing a code generation task.

    Args:
        task_data: Parsed task data dictionary

    Returns:
        Processing result dictionary
    """
    # Initialize the code generator
    generator = E2BClaudeCodeGenerator()

    # Process the task
    result = await generator.process_task(task_data)

    return result


async def main():
    """Test the E2B Claude Code handler with a simple example."""
    test_task = {
        "task_id": "test_hello_world",
        "specification": "Build a simple Python Flask web application with a home page that displays 'Hello, World!' and the current time"
    }

    print("\n" + "="*60)
    print("  E2B Claude Code Handler Test")
    print("="*60)
    print(f"  Specification: {test_task['specification']}")
    print("="*60 + "\n")

    result = await process_sqs_message_async(test_task)

    print("\nTask Result:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    # Run the test
    asyncio.run(main())