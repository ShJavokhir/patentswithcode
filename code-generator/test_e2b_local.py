#!/usr/bin/env python3
"""
Local test script for E2B code generation without SQS.
Run this to test the E2B handler directly.
"""
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

from e2b_handler import E2BCodeGenerator


def test_simple_hello_world():
    """Test generating a simple hello world application."""
    print("\n" + "="*60)
    print("Test 1: Simple Hello World Application")
    print("="*60)

    task = {
        "task_id": "test_hello_world",
        "specification": "Build a simple hello world Python script that prints 'Hello, World!' and the current date"
    }

    generator = E2BCodeGenerator()
    result = generator.process_task(task)

    print_result(result)
    return result['status'] == 'completed'


def test_flask_app():
    """Test generating a Flask web application."""
    print("\n" + "="*60)
    print("Test 2: Flask Web Application")
    print("="*60)

    task = {
        "task_id": "test_flask_app",
        "specification": "Build a simple Flask web application with a home route that returns 'Hello, World!' and an about route that returns 'About Page'"
    }

    generator = E2BCodeGenerator()
    result = generator.process_task(task)

    print_result(result)
    return result['status'] == 'completed'


def test_calculator():
    """Test generating a calculator application."""
    print("\n" + "="*60)
    print("Test 3: Calculator Application")
    print("="*60)

    task = {
        "task_id": "test_calculator",
        "specification": "Build a simple calculator Python module with functions for add, subtract, multiply, and divide operations"
    }

    generator = E2BCodeGenerator()
    result = generator.process_task(task)

    print_result(result)
    return result['status'] == 'completed'


def print_result(result):
    """Print the test result in a formatted way."""
    print(f"\nTask ID: {result.get('task_id')}")
    print(f"Status: {result.get('status')}")

    if result.get('status') == 'completed':
        print("\n✓ Task completed successfully!")

        if result.get('implementation_plan'):
            print("\nImplementation Plan:")
            print("-" * 40)
            print(result['implementation_plan'][:500] + "..." if len(result['implementation_plan']) > 500 else result['implementation_plan'])

        if result.get('files_created'):
            print("\nFiles Created:")
            for file in result['files_created']:
                print(f"  - {file}")

        if result.get('generated_code'):
            print("\nGenerated Code Preview:")
            print("-" * 40)
            code_preview = result['generated_code'][:500] + "..." if len(result['generated_code']) > 500 else result['generated_code']
            print(code_preview)

        logs = result.get('execution_logs', {})
        if logs.get('execution_output'):
            print("\nExecution Output:")
            print("-" * 40)
            print(logs['execution_output'][:500] + "..." if len(logs['execution_output']) > 500 else logs['execution_output'])

    else:
        print(f"\n✗ Task failed: {result.get('error')}")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("  E2B Code Generator - Local Test Suite")
    print("="*60)

    tests = [
        ("Simple Hello World", test_simple_hello_world),
        ("Flask Application", test_flask_app),
        ("Calculator Module", test_calculator)
    ]

    results = []
    for test_name, test_func in tests:
        try:
            print(f"\nRunning: {test_name}...")
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"Error in {test_name}: {e}")
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
    success = main()
    sys.exit(0 if success else 1)