#!/usr/bin/env python3
"""Test script for React component generation."""

from e2b_simple import SimpleE2BGenerator

def main():
    """Test React component generation."""
    generator = SimpleE2BGenerator()

    # Test with a React calculator component
    task = {
        "task_id": "test_calculator",
        "specification": "Create a simple React calculator component with add, subtract, multiply, divide functions. Use TypeScript and include styled components with Tailwind CSS classes."
    }

    print("\n" + "="*60)
    print(f"Testing: {task['specification'][:50]}...")
    print("="*60)

    result = generator.process_task(task)

    print(f"\nStatus: {result.get('status')}")
    if result.get('status') == 'completed':
        print(f"Files created: {result.get('files_created', [])}")
        if result.get('local_archive'):
            print(f"Local archive: {result.get('local_archive')}")
        if result.get('s3_url'):
            print(f"S3 URL: {result.get('s3_url')}")
        print(f"Execution output: {result.get('execution_output', 'No output')[:200]}")
    else:
        print(f"Error: {result.get('error')}")

    return result

if __name__ == "__main__":
    result = main()

    # Extract and display the generated files
    if result.get('status') == 'completed' and result.get('local_archive'):
        import subprocess
        print("\n" + "="*60)
        print("Generated Files:")
        print("="*60)

        # List archive contents
        archive_path = result['local_archive']
        listing = subprocess.run(f"tar -tzf {archive_path}", shell=True, capture_output=True, text=True)
        print(listing.stdout)

        # Extract first React file
        for file in listing.stdout.strip().split('\n'):
            if file.endswith('.jsx') or file.endswith('.tsx'):
                print(f"\n--- Content of {file} ---")
                content = subprocess.run(f"tar -xOf {archive_path} {file}", shell=True, capture_output=True, text=True)
                print(content.stdout[:1000])  # Show first 1000 chars
                break