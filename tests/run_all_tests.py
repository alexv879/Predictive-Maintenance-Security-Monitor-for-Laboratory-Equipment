#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Master test runner for Premonitor project.
Runs all test suites and reports overall status.
"""

import sys
import subprocess
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent


def run_test_file(test_file, description):
    """Run a test file and report results."""
    print(f"\n{'=' * 60}")
    print(f"Running: {description}")
    print('=' * 60)

    try:
        result = subprocess.run(
            [sys.executable, str(test_file)],
            cwd=str(project_root),
            capture_output=False,
            text=True
        )
        return result.returncode == 0
    except Exception as e:
        print(f"[ERROR] Failed to run {test_file}: {e}")
        return False


def main():
    """Run all test suites."""
    print("=" * 60)
    print("PREMONITOR - MASTER TEST SUITE")
    print("=" * 60)

    tests_dir = project_root / 'tests'

    test_suites = [
        (tests_dir / 'test_datasets.py', 'Dataset Validation Tests'),
        (tests_dir / 'test_imports.py', 'Module Import Tests'),
        (tests_dir / 'test_equipment_registry.py', 'Equipment Registry Tests'),
    ]

    results = []
    for test_file, description in test_suites:
        if test_file.exists():
            success = run_test_file(test_file, description)
            results.append((description, success))
        else:
            print(f"\n[WARN] Test file not found: {test_file}")
            results.append((description, False))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for description, success in results:
        status = "[PASS]" if success else "[FAIL]"
        print(f"{status} {description}")

    passed = sum(1 for _, success in results if success)
    total = len(results)

    print("=" * 60)
    print(f"Overall: {passed}/{total} test suites passed")
    print("=" * 60)

    return 0 if passed == total else 1


if __name__ == '__main__':
    sys.exit(main())
