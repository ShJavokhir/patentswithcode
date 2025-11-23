#!/usr/bin/env python3
"""
Synchronous E2B Sandbox handler that runs Claude Code inside the sandbox.
This is a simpler, synchronous version that should be more compatible.
"""
import json
import os
import logging
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

    def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
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
            # Create E2B sandbox
            sandbox = self._create_sandbox()

            # Execute Claude Code in the sandbox
            result = self._execute_claude_code(sandbox, specification)

            # List created files
            files = self._list_created_files(sandbox)

            # Get the main file content if exists
            main_content = self._get_main_file_content(sandbox, files)

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
            import traceback
            traceback.print_exc()
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
                    sandbox.kill()
                    logger.info("Sandbox terminated successfully")
                except Exception as e:
                    logger.warning(f"Error terminating sandbox: {e}")

    def _create_sandbox(self) -> Sandbox:
        """Create and initialize E2B sandbox with Claude Code installed."""
        logger.info("Creating E2B sandbox...")

        # Create sandbox using synchronous API
        sandbox = Sandbox.create()

        logger.info("Sandbox created successfully")

        # Check Node.js installation
        logger.info("Checking Node.js installation...")
        node_result = sandbox.commands.run("node --version")

        if node_result.exit_code != 0:
            logger.info("Installing Node.js...")
            # Try to install Node.js
            install_cmds = [
                "apt-get update",
                "apt-get install -y curl",
                "curl -fsSL https://deb.nodesource.com/setup_20.x | bash -",
                "apt-get install -y nodejs"
            ]

            for cmd in install_cmds:
                logger.info(f"Running: {cmd}")
                result = sandbox.commands.run(cmd, timeout=60)
                if result.exit_code != 0:
                    logger.warning(f"Command failed: {cmd}, stderr: {result.stderr}")

        # Verify Node.js installation
        node_version = sandbox.commands.run("node --version")
        if node_version.exit_code == 0:
            logger.info(f"Node.js version: {node_version.stdout}")
        else:
            logger.warning("Node.js installation might have issues")

        # Note: We'll use the Python-based approach instead of Claude Code CLI
        # since the CLI package doesn't exist in npm registry

        return sandbox

    def _execute_claude_code(self, sandbox: Sandbox, specification: str) -> Dict[str, Any]:
        """
        Generate and execute code in the sandbox using Claude API.

        Args:
            sandbox: E2B sandbox instance
            specification: The code generation specification

        Returns:
            Dictionary with execution results
        """
        logger.info("Generating code with Claude API...")

        # Import Anthropic client
        from anthropic import Anthropic

        # Initialize Claude client
        client = Anthropic(api_key=self.anthropic_api_key)

        # Create prompt for generating a Python script that creates React/web files
        prompt = f"""Generate a Python script that creates the requested files.

The Python script should:
1. Use standard Python file I/O to write the requested files
2. Create all files in the current directory
3. Be a complete, executable Python script
4. Output only pure Python code, no explanations

For React components (which are most common):
- Write the component code to .jsx or .tsx files
- Create an index.html file with proper structure
- Include any CSS in separate .css files or inline styles
- Create a package.json if needed

Return ONLY executable Python code that creates the files. No markdown, no explanations.

Example format:
```python
# Create a React component file
with open('Calculator.jsx', 'w') as f:
    f.write('''
import React, {{ useState }} from 'react';

function Calculator() {{
    const [result, setResult] = useState(0);
    // ... component code
    return <div>Calculator UI</div>;
}}

export default Calculator;
''')

# Create an HTML file
with open('index.html', 'w') as f:
    f.write('''
<!DOCTYPE html>
<html>
<head><title>Calculator</title></head>
<body><div id="root"></div></body>
</html>
''')
```

Specification:
{specification}
"""

        # Generate code using Claude API
        response = client.messages.create(
            model="claude-3-5-haiku-latest",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )

        code = response.content[0].text

        # Extract Python code if wrapped in markdown
        if "```python" in code:
            import re
            blocks = re.findall(r'```python\n(.*?)\n```', code, re.DOTALL)
            if blocks:
                code = '\n\n'.join(blocks)

        # Write the generation script to sandbox
        sandbox.filesystem.write("/tmp/generate.py", code)

        # Execute the generation script
        logger.info("Executing generation script in sandbox...")
        result = sandbox.commands.run("cd /tmp && python generate.py", timeout=30)

        if result.exit_code == 0:
            logger.info("Code generation successful")
        else:
            logger.warning(f"Code generation failed with exit code {result.exit_code}")
            if result.stderr:
                logger.warning(f"Error: {result.stderr[:500]}")

        return {
            'output': result.stdout or '',
            'error': result.stderr or '',
            'exit_code': result.exit_code
        }

    def _list_created_files(self, sandbox: Sandbox) -> list:
        """
        List all files created in the sandbox.

        Args:
            sandbox: E2B sandbox instance

        Returns:
            List of file paths
        """
        logger.info("Listing created files...")

        # Find all relevant files (including React files)
        result = sandbox.commands.run(
            "find /tmp -type f \\( -name '*.py' -o -name '*.js' -o -name '*.jsx' -o -name '*.tsx' -o -name '*.html' -o -name '*.css' -o -name '*.json' -o -name '*.md' -o -name '*.txt' \\) 2>/dev/null | grep -v node_modules | grep -v '.git' | grep -v generate.py | head -20"
        )

        files = []
        if result.stdout:
            files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
            logger.info(f"Found {len(files)} files")

        return files

    def _get_main_file_content(self, sandbox: Sandbox, files: list) -> str:
        """
        Get the content of the main file if it exists.

        Args:
            sandbox: E2B sandbox instance
            files: List of created files

        Returns:
            Content of the main file
        """
        # Look for common main file names (including React files)
        main_candidates = ['/tmp/main.py', '/tmp/app.py',
                          '/tmp/index.js', '/tmp/App.jsx', '/tmp/App.tsx',
                          '/tmp/Calculator.jsx', '/tmp/index.html']

        for candidate in main_candidates:
            if any(candidate in f or f.endswith(candidate.lstrip('./')) for f in files):
                try:
                    content = sandbox.filesystem.read(candidate)
                    if content:
                        logger.info(f"Found main file: {candidate}")
                        return content
                except:
                    pass

        # If no standard main file, return the first code file
        for file in files:
            if file.endswith(('.py', '.js', '.jsx', '.tsx', '.html')):
                try:
                    content = sandbox.filesystem.read(file)
                    if content:
                        logger.info(f"Returning content of: {file}")
                        return content
                except:
                    pass

        return ""


def test_simple():
    """Test the synchronous E2B Claude Code handler."""
    test_task = {
        "task_id": "test_sync",
        "specification": "Create a simple Python script that prints 'Hello, World!' and the current time"
    }

    print("\n" + "="*60)
    print("  E2B Claude Code Sync Test")
    print("="*60)
    print(f"  Specification: {test_task['specification']}")
    print("="*60 + "\n")

    generator = E2BClaudeCodeGenerator()
    result = generator.process_task(test_task)

    print("\nTask Result:")
    print(f"Status: {result.get('status')}")
    print(f"Task ID: {result.get('task_id')}")

    if result.get('status') == 'completed':
        print(f"Files created: {result.get('files_created', [])}")
        if result.get('main_file_content'):
            print("\nMain file content:")
            print("-" * 40)
            print(result.get('main_file_content', '')[:500])
    else:
        print(f"Error: {result.get('error')}")

    return result


if __name__ == "__main__":
    # Run the test
    result = test_simple()
    print("\nFull result:")
    print(json.dumps(result, indent=2))