#!/usr/bin/env python3
"""
Simple E2B Sandbox handler for code generation using Claude API.
This version uses Python inside the sandbox to generate code with Claude.
"""
import json
import os
import logging
import tempfile
import tarfile
from typing import Dict, Any, Optional
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
from e2b import Sandbox
from anthropic import Anthropic
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SimpleE2BGenerator:
    """Simple code generator using E2B sandbox and Claude API."""

    def __init__(self):
        """Initialize the configuration."""
        load_dotenv()

        # Set E2B API key
        self.e2b_api_key = os.getenv('E2B_API_KEY')
        if self.e2b_api_key:
            os.environ['E2B_API_KEY'] = self.e2b_api_key
        else:
            raise ValueError("E2B_API_KEY is required")

        # Initialize Claude client for generating code
        self.anthropic = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        if not os.getenv('ANTHROPIC_API_KEY'):
            raise ValueError("ANTHROPIC_API_KEY is required")

        # Initialize S3 client (optional - will work without S3)
        self.s3_enabled = False
        self.s3_bucket = os.getenv('S3_BUCKET', 'watchlearn1')

        try:
            self.s3_client = boto3.client('s3', region_name=os.getenv('AWS_REGION', 'us-east-1'))
            # Test bucket access
            self.s3_client.head_bucket(Bucket=self.s3_bucket)
            self.s3_enabled = True
            logger.info(f"S3 bucket configured: {self.s3_bucket}")
        except ClientError as e:
            logger.warning(f"S3 not available: {e}. Will continue without S3 uploads.")
            self.s3_client = None

    def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a code generation task.

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
            # Generate code with Claude first
            logger.info("Generating code with Claude...")
            generated_code = self._generate_code(specification)

            # Create E2B sandbox
            logger.info("Creating E2B sandbox...")
            sandbox = Sandbox.create()
            logger.info("Sandbox created successfully")

            # Execute the generated code in sandbox
            logger.info("Executing code in sandbox...")
            execution_result = self._execute_in_sandbox(sandbox, generated_code)

            # List created files
            files = self._list_created_files(sandbox)

            # Create archive of generated files and upload to S3 if enabled
            s3_url = None
            archive_path = None

            # Always try to create local archive (even if no files found by find command)
            archive_path = self._create_local_archive(sandbox, files, task_id)

            # Try S3 upload if enabled and archive was created
            if self.s3_enabled and self.s3_client and archive_path:
                logger.info(f"Uploading archive to S3...")
                s3_url = self._upload_to_s3(archive_path, task_id)

            return {
                'task_id': task_id,
                'status': 'completed',
                'specification': specification,
                'files_created': files,
                's3_url': s3_url,
                'local_archive': archive_path,
                'execution_output': execution_result.get('output', ''),
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
            if sandbox:
                try:
                    sandbox.kill()
                    logger.info("Sandbox closed")
                except:
                    pass

    def _generate_code(self, specification: str) -> str:
        """Generate code using Claude API."""
        prompt = f"""Generate a Python script that creates the requested files based on the specification.

IMPORTANT: You must generate PYTHON code that writes the requested files. The Python code will be executed to create the files.

For React/JavaScript projects, the Python script should:
1. Use open() and write() to create .jsx, .tsx, .js, .html, .css files
2. Write the React/JavaScript code as string literals in Python
3. Use triple quotes for multi-line strings
4. Use forward slash / for division, NOT ÷
5. Properly escape curly braces in f-strings and React code

Example for a calculator:
```python
# Create Calculator.jsx
with open('Calculator.jsx', 'w') as f:
    f.write('''import React, {{ useState }} from 'react';

function Calculator() {{
    const [num1, setNum1] = useState(0);
    const [num2, setNum2] = useState(0);
    const [result, setResult] = useState(0);

    const divide = () => {{
        if (num2 !== 0) {{
            setResult(num1 / num2);  // Use / for division, not ÷
        }}
    }};

    return (
        <div className="calculator">
            <input type="number" value={{num1}} onChange={{e => setNum1(Number(e.target.value))}} />
            <input type="number" value={{num2}} onChange={{e => setNum2(Number(e.target.value))}} />
            <button onClick={{divide}}>/</button>
            <div>Result: {{result}}</div>
        </div>
    );
}}

export default Calculator;''')

# Create index.html
with open('index.html', 'w') as f:
    f.write('''<!DOCTYPE html>
<html lang="en">
<head>
    <title>Calculator</title>
</head>
<body>
    <div id="root"></div>
</body>
</html>''')

print("Files created successfully")
```

Return ONLY the Python code, no markdown wrapper, no explanations.

Specification:
{specification}
"""

        response = self.anthropic.messages.create(
            model="claude-3-5-haiku-latest",
            max_tokens=8000,
            messages=[{"role": "user", "content": prompt}]
        )

        code = response.content[0].text

        # Extract Python code if wrapped in markdown
        if "```python" in code:
            import re
            blocks = re.findall(r'```python\n(.*?)\n```', code, re.DOTALL)
            if blocks:
                code = '\n\n'.join(blocks)
        elif "```" in code:
            # Remove any other markdown code blocks
            import re
            code = re.sub(r'```\w*\n', '', code)
            code = code.replace('```', '')

        # Fix common issues
        code = code.replace('÷', '/')  # Replace division symbol with forward slash

        return code

    def _execute_in_sandbox(self, sandbox: Sandbox, code: str) -> Dict[str, Any]:
        """Execute the generated code in the sandbox."""
        # First create the Python script that will generate files
        create_script = f"""
cat > /tmp/generate.py << 'EOF'
{code}
EOF
"""
        # Write the generation script
        sandbox.commands.run(create_script)

        # Execute the code
        result = sandbox.commands.run("cd /tmp && python generate.py", timeout=30)

        return {
            'output': result.stdout or '',
            'error': result.stderr or '',
            'exit_code': result.exit_code
        }

    def _list_created_files(self, sandbox: Sandbox) -> list:
        """List files created in /tmp directory."""
        result = sandbox.commands.run(
            "find /tmp -type f \\( -name '*.py' -o -name '*.js' -o -name '*.jsx' -o -name '*.tsx' -o -name '*.html' -o -name '*.css' -o -name '*.json' -o -name '*.md' -o -name '*.txt' \\) | grep -v generate.py | head -20"
        )

        files = []
        if result.stdout:
            files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]

        return files

    def _create_local_archive(self, sandbox: Sandbox, files: list, task_id: str) -> str:
        """
        Create a local tar archive of all generated files.

        Args:
            sandbox: E2B sandbox instance
            files: List of file paths to archive
            task_id: Task identifier

        Returns:
            Path to local archive file
        """
        try:
            # Create archive in sandbox
            archive_name = f"{task_id}.tar.gz"
            archive_path = f"/tmp/{archive_name}"

            # If no files found with find, try to archive everything in /tmp
            if not files:
                logger.info("No files found with find command, archiving all /tmp files")
                tar_command = f"cd /tmp && tar -czf {archive_name} --exclude={archive_name} --exclude=generate.py * 2>/dev/null || tar -czf {archive_name} --exclude={archive_name} --exclude=generate.py ."
            else:
                # Extract just the filenames without /tmp/ prefix
                clean_files = []
                for f in files:
                    if f.startswith('/tmp/'):
                        clean_files.append(f[5:])  # Remove '/tmp/' prefix
                    else:
                        clean_files.append(f)

                # Skip if only generate.py exists
                if clean_files == ['generate.py'] or not clean_files:
                    logger.info("No user files to archive (only generate.py found)")
                    # Try to archive everything except generate.py
                    tar_command = f"cd /tmp && tar -czf {archive_name} --exclude={archive_name} --exclude=generate.py * 2>/dev/null || tar -czf {archive_name} --exclude={archive_name} --exclude=generate.py ."
                else:
                    files_str = ' '.join([f'"{f}"' for f in clean_files if f != 'generate.py'])
                    tar_command = f"cd /tmp && tar -czf {archive_name} {files_str}"

            logger.info(f"Creating archive: {archive_name}")
            logger.debug(f"Tar command: {tar_command}")
            result = sandbox.commands.run(tar_command)

            # Even if tar returns non-zero, check if archive was created
            check_archive = sandbox.commands.run(f"ls -la {archive_path} 2>/dev/null")
            if check_archive.exit_code != 0 or not check_archive.stdout:
                # Fallback: Try archiving with a simpler command
                logger.info("Initial archive failed, trying fallback method")

                # First, list what's actually in /tmp
                ls_result = sandbox.commands.run("ls -la /tmp/ | grep -v '^d' | grep -v '^total' | awk '{print $9}' | grep -v '^$'")
                if ls_result.stdout:
                    actual_files = [f.strip() for f in ls_result.stdout.strip().split('\n')
                                  if f.strip() and f.strip() not in ['generate.py', archive_name, '.', '..']]

                    if actual_files:
                        # Create archive with actual files found
                        files_str = ' '.join([f'"{f}"' for f in actual_files])
                        fallback_cmd = f"cd /tmp && tar -czf {archive_name} {files_str} 2>&1"
                        logger.info(f"Found files to archive: {actual_files}")
                        result = sandbox.commands.run(fallback_cmd)

            # Create local archives directory
            os.makedirs('archives', exist_ok=True)
            local_archive_path = f"archives/{archive_name}"

            # Download archive from sandbox
            with open(local_archive_path, 'wb') as f:
                # Get archive content using base64 encoding to handle binary data
                get_archive = sandbox.commands.run(f"base64 {archive_path} 2>/dev/null")

                if get_archive.exit_code == 0 and get_archive.stdout:
                    import base64
                    archive_data = base64.b64decode(get_archive.stdout)
                    f.write(archive_data)
                    logger.info(f"Archive saved locally: {local_archive_path}")
                    return local_archive_path
                else:
                    logger.error("Failed to retrieve archive from sandbox")
                    return None

        except Exception as e:
            logger.error(f"Archive creation failed: {e}")
            return None

    def _upload_to_s3(self, archive_path: str, task_id: str) -> str:
        """
        Upload archive to S3 root folder.

        Args:
            archive_path: Path to local archive file
            task_id: Task identifier

        Returns:
            S3 URL of the uploaded archive
        """
        if not archive_path or not os.path.exists(archive_path):
            return None

        try:
            # Simple naming: task_id.tar.gz in root folder
            s3_key = f"{task_id}.tar.gz"

            logger.info(f"Uploading to S3: s3://{self.s3_bucket}/{s3_key}")
            self.s3_client.upload_file(
                archive_path,
                self.s3_bucket,
                s3_key,
                ExtraArgs={
                    'ContentType': 'application/gzip',
                    'Metadata': {
                        'task_id': task_id,
                        'generated_at': datetime.now().isoformat()
                    }
                }
            )

            # Generate S3 URL
            s3_url = f"s3://{self.s3_bucket}/{s3_key}"
            logger.info(f"Successfully uploaded to: {s3_url}")
            return s3_url

        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            return None


def main():
    """Test the simple E2B handler."""
    test_tasks = [
        {
            "task_id": "test_hello",
            "specification": "Create a simple Python script hello.py that prints 'Hello, World!' and the current date"
        },
        {
            "task_id": "test_calculator",
            "specification": "Create a Python calculator module with add, subtract, multiply, divide functions in calculator.py"
        }
    ]

    generator = SimpleE2BGenerator()

    for task in test_tasks:
        print("\n" + "="*60)
        print(f"Testing: {task['specification'][:50]}...")
        print("="*60)

        result = generator.process_task(task)

        print(f"\nStatus: {result.get('status')}")
        if result.get('status') == 'completed':
            print(f"Files created: {len(result.get('files_created', []))} files")
            if result.get('local_archive'):
                print(f"Local archive: {result.get('local_archive')}")
            if result.get('s3_url'):
                print(f"S3 URL: {result.get('s3_url')}")
            print(f"Execution output: {result.get('execution_output', 'No output')[:200]}")
        else:
            print(f"Error: {result.get('error')}")

        # Only test first one for now
        break


if __name__ == "__main__":
    main()