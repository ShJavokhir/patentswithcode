#!/usr/bin/env python3
"""
Test script for E2B Claude Code integration.
Tests the Claude Code CLI running inside E2B sandbox.
"""
import asyncio
import json
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check for required environment variables
required_vars = ['E2B_API_KEY', 'ANTHROPIC_API_KEY']
missing_vars = [var for var in required_vars if not os.getenv(var)]

if missing_vars:
    print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
    print("Please set them in your .env file")
    sys.exit(1)

from e2b_claude_handler import E2BClaudeCodeGenerator


async def test_simple_hello_world():
    """Test generating a simple hello world application."""
    print("\n" + "="*60)
    print("Test 1: Simple Hello World Script")
    print("="*60)

    task = {
        "task_id": "test_hello",
        "specification": "Create a simple Python script called hello.py that prints 'Hello, World!' and shows the current date and time"
    }

    generator = E2BClaudeCodeGenerator()
    result = await generator.process_task(task)

    print_result(result)
    return result.get('status') == 'completed'


async def test_flask_api():
    """Test generating a Flask REST API."""
    print("\n" + "="*60)
    print("Test 2: Flask REST API")
    print("="*60)

    task = {
        "task_id": "test_flask",
        "specification": """Create a simple Flask REST API with the following endpoints:
        - GET / returns {'message': 'Welcome to the API'}
        - GET /health returns {'status': 'healthy'}
        - GET /time returns the current server time
        Create app.py and requirements.txt files"""
    }

    generator = E2BClaudeCodeGenerator()
    result = await generator.process_task(task)

    print_result(result)
    return result.get('status') == 'completed'


async def test_calculator_module():
    """Test generating a calculator module."""
    print("\n" + "="*60)
    print("Test 3: Calculator Module")
    print("="*60)

    task = {
        "task_id": "test_calc",
        "specification": """Create a Python calculator module with the following:
        - calculator.py with functions: add, subtract, multiply, divide
        - test_calculator.py with unit tests for all functions
        - README.md with usage examples"""
    }

    generator = E2BClaudeCodeGenerator()
    result = await generator.process_task(task)

    print_result(result)
    return result.get('status') == 'completed'


def print_result(result):
    """Print the test result in a formatted way."""
    print(f"\nTask ID: {result.get('task_id')}")
    print(f"Status: {result.get('status')}")
    print(f"Timestamp: {result.get('timestamp')}")

    if result.get('status') == 'completed':
        print("\n✓ Task completed successfully!")

        if result.get('files_created'):
            print(f"\nFiles Created ({len(result.get('files_created', []))} files):")
            for file in result.get('files_created', [])[:10]:
                print(f"  - {file}")
            if len(result.get('files_created', [])) > 10:
                print(f"  ... and {len(result.get('files_created', [])) - 10} more files")

        if result.get('main_file_content'):
            print("\nMain File Content Preview:")
            print("-" * 40)
            content = result.get('main_file_content', '')
            preview = content[:500] + "..." if len(content) > 500 else content
            print(preview)

        if result.get('execution_output'):
            print("\nExecution Output Preview:")
            print("-" * 40)
            output = result.get('execution_output', '')
            preview = output[:300] + "..." if len(output) > 300 else output
            print(preview)

    else:
        print(f"\n✗ Task failed: {result.get('error', 'Unknown error')}")


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("  E2B Claude Code Test Suite")
    print("="*60)
    print("  Testing Claude Code CLI in E2B Sandbox")
    print("="*60)

    tests = [
        ("Simple Hello World", test_simple_hello_world),
        ("Flask REST API", test_flask_api),
        ("Calculator Module", test_calculator_module)
    ]

    results = []

    for test_name, test_func in tests:
        try:
            print(f"\nRunning: {test_name}...")
            success = await test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"Error in {test_name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # Print summary
    print("\n" + "="*60)
    print("  Test Summary")
    print("="*60)

    for test_name, success in results:
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"{status}: {test_name}")

    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")

    return passed == total


if __name__ == "__main__":
    # Run the async main function
    success = asyncio.run(main())
    sys.exit(0 if success else 1)