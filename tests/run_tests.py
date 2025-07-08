#!/usr/bin/env python3
"""
Comprehensive Test Runner for Telegram University Bot v2.1.0
Runs all tests from organized test folders
"""

import sys
import os
import subprocess
import re


def run_pytest_tests():
    """Run all pytest-based tests"""
    print("🧪 Running Pytest Tests...")
    print("=" * 50)

    # Add the project root to Python path
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)

    # Set environment variables for consistent testing
    SEMVER_REGEX = r'^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$'
    env = os.environ.copy()
    raw_version = os.getenv("BOT_VERSION", "2.1.0")
    if re.match(SEMVER_REGEX, raw_version):
        validated_version = raw_version
    else:
        validated_version = "v2.1.0"
    env["BOT_VERSION"] = validated_version

    # Run pytest on all test directories
    test_dirs = ["tests/storage", "tests/security", "tests/api"]

    all_passed = True
    for test_dir in test_dirs:
        if os.path.exists(test_dir):
            print(f"\n📁 Testing {test_dir}:")
            result = subprocess.run(
                [sys.executable, "-m", "pytest", test_dir, "-v"],
                capture_output=True,
                text=True,
                env=env,
            )

            if result.returncode == 0:
                print("✅ All tests passed")
            else:
                print("❌ Some tests failed")
                print(result.stdout)
                all_passed = False

    return all_passed


def run_manual_tests():
    """Run manual test scripts"""
    print("\n🔧 Running Manual Tests...")
    print("=" * 50)

    # Add the project root to Python path
    project_root = os.path.dirname(os.path.abspath(__file__))

    # Set environment variables for consistent testing
    env = os.environ.copy()
    env["BOT_VERSION"] = "v2.1.0"

    manual_tests = [
        ("tests/api/test_api_quotes.py", "API Quote Tests"),
        ("tests/security/test_password_security.py", "Password Security Tests"),
    ]

    all_passed = True
    for test_file, test_name in manual_tests:
        if os.path.exists(test_file):
            print(f"\n📋 Running {test_name}:")
            # Set PYTHONPATH for proper module imports
            env["PYTHONPATH"] = project_root
            result = subprocess.run(
                [sys.executable, test_file], capture_output=True, text=True, env=env
            )

            if result.returncode == 0:
                print("✅ Test passed")
            else:
                print("❌ Test failed")
                print(result.stdout)
                all_passed = False

    return all_passed


def main():
    """Main test runner"""
    print(f"\U0001F680 Telegram University Bot v{os.getenv('BOT_VERSION', 'v2.1.0')} - Comprehensive Test Suite")
    print("=" * 60)

    # Run pytest tests
    pytest_passed = run_pytest_tests()

    # Run manual tests
    manual_passed = run_manual_tests()

    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    print(f"Pytest Tests: {'✅ PASSED' if pytest_passed else '❌ FAILED'}")
    print(f"Manual Tests: {'✅ PASSED' if manual_passed else '❌ FAILED'}")

    if pytest_passed and manual_passed:
        print("\n🎉 All tests passed! Project is ready for deployment.")
        return 0
    else:
        print("\n⚠️ Some tests failed. Please review and fix issues.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
