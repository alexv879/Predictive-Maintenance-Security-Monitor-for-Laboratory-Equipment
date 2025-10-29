#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Dataset smoke tests for Premonitor project.

NOTE: This test requires datasets to be downloaded locally.
Datasets are NOT included in the repository due to size (~82 GB).

To download datasets, see: docs/DATASETS_DOWNLOAD_GUIDE.md

This test is skipped in CI by default.
"""

import sys
import os
from pathlib import Path
import csv

# Add project root to path
project_root = Path(__file__).resolve().parent.parent


def test_esc50_dataset():
    """Test ESC-50 dataset is accessible."""
    esc50_csv = project_root / 'datasets' / 'datasets audio' / 'ESC-50-master' / 'ESC-50-master' / 'meta' / 'esc50.csv'
    esc50_audio = project_root / 'datasets' / 'datasets audio' / 'ESC-50-master' / 'ESC-50-master' / 'audio'

    if not esc50_csv.exists():
        print(f"[FAIL] ESC-50 metadata not found: {esc50_csv}")
        return False

    if not esc50_audio.exists():
        print(f"[FAIL] ESC-50 audio directory not found: {esc50_audio}")
        return False

    # Try to read CSV
    try:
        with open(esc50_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            if len(rows) > 0:
                # Check expected columns
                expected_cols = {'filename', 'fold', 'target', 'category'}
                if expected_cols.issubset(rows[0].keys()):
                    print(f"[PASS] ESC-50 dataset valid ({len(rows)} entries)")
                    return True
                else:
                    print(f"[FAIL] ESC-50 CSV missing expected columns")
                    return False
            else:
                print(f"[FAIL] ESC-50 CSV is empty")
                return False
    except Exception as e:
        print(f"[FAIL] Failed to read ESC-50 CSV: {e}")
        return False


def test_urbansound8k_dataset():
    """Test UrbanSound8K dataset metadata is accessible."""
    urbansound_csv = project_root / 'datasets' / 'datasets audio' / 'urbansound8kdataset' / 'UrbanSound8K.csv'

    if not urbansound_csv.exists():
        print(f"[WARN] UrbanSound8K metadata not found (may need extraction): {urbansound_csv}")
        return True  # Not critical, just a warning

    try:
        with open(urbansound_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            if len(rows) > 0:
                expected_cols = {'slice_file_name', 'fold', 'classID', 'class'}
                if expected_cols.issubset(rows[0].keys()):
                    print(f"[PASS] UrbanSound8K dataset valid ({len(rows)} entries)")
                    return True
                else:
                    print(f"[FAIL] UrbanSound8K CSV missing expected columns")
                    return False
            else:
                print(f"[FAIL] UrbanSound8K CSV is empty")
                return False
    except Exception as e:
        print(f"[FAIL] Failed to read UrbanSound8K CSV: {e}")
        return False


def test_thermal_dataset():
    """Test thermal dataset is accessible."""
    trimodal_dir = project_root / 'datasets' / 'thermal camera dataset' / 'trimodaldataset' / 'TrimodalDataset'

    if not trimodal_dir.exists():
        print(f"[FAIL] Trimodal dataset directory not found: {trimodal_dir}")
        return False

    # Check for scenes
    scenes = [d for d in trimodal_dir.iterdir() if d.is_dir() and d.name.startswith('Scene')]
    if len(scenes) == 0:
        print(f"[FAIL] No scenes found in trimodal dataset")
        return False

    # Check that at least one scene has some data
    for scene in scenes:
        annotations = scene / 'annotations.csv'
        if annotations.exists():
            print(f"[PASS] Thermal dataset valid ({len(scenes)} scenes)")
            return True

    print(f"[FAIL] No valid scenes with annotations found")
    return False


def run_all_tests():
    """Run all dataset tests."""
    print("=" * 60)
    print("PREMONITOR SMOKE TESTS - Dataset Validation")
    print("=" * 60)

    tests = [
        test_esc50_dataset,
        test_urbansound8k_dataset,
        test_thermal_dataset,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"[FAIL] Test {test.__name__} crashed: {e}")
            results.append(False)

    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)

    return all(results)


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
