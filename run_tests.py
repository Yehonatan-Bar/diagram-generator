#!/usr/bin/env python3
"""
Test runner script for the diagram-generator project.

Usage:
    python run_tests.py              # Run all tests
    python run_tests.py unit         # Run only unit tests
    python run_tests.py integration  # Run only integration tests
    python run_tests.py coverage     # Run with coverage report
"""
import sys
import subprocess
import os


def run_command(cmd):
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode


def main():
    """Main test runner."""
    # Ensure we're in the project root
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Set test environment
    os.environ["USE_MOCK_LLM"] = "true"
    os.environ["ENVIRONMENT"] = "test"
    os.environ["LOG_LEVEL"] = "WARNING"
    
    # Default to running all tests
    test_type = sys.argv[1] if len(sys.argv) > 1 else "all"
    
    if test_type == "unit":
        # Run unit tests only
        cmd = ["pytest", "tests/unit/", "-v"]
    elif test_type == "integration":
        # Run integration tests only
        cmd = ["pytest", "tests/integration/", "-v"]
    elif test_type == "coverage":
        # Run with coverage
        cmd = [
            "pytest",
            "--cov=src",
            "--cov-report=html",
            "--cov-report=term-missing",
            "-v"
        ]
    elif test_type == "all":
        # Run all tests
        cmd = ["pytest", "-v"]
    else:
        print(f"Unknown test type: {test_type}")
        print(__doc__)
        return 1
    
    # Run the tests
    return run_command(cmd)


if __name__ == "__main__":
    sys.exit(main())