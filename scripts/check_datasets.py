#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Dataset Validation Tool for Premonitor Project

This script validates the presence and structure of all datasets required
for the Premonitor AI anomaly detection system.

Usage:
    python scripts/check_datasets.py [--verbose]

Exit Codes:
    0 - All required datasets present and valid
    1 - One or more required datasets missing or invalid
    2 - Script error
"""

import os
import sys
import argparse
import csv
import json
from pathlib import Path
from collections import defaultdict


class DatasetValidator:
    """Validates dataset presence and structure for Premonitor project."""

    def __init__(self, base_dir, verbose=False):
        self.base_dir = Path(base_dir)
        self.verbose = verbose
        self.errors = []
        self.warnings = []
        self.stats = {}

    def log(self, message, level='info'):
        """Print message if verbose mode enabled."""
        if self.verbose or level in ['error', 'warning']:
            prefix = {
                'info': '[INFO]',
                'warning': '[WARNING]',
                'error': '[ERROR]',
                'success': '[SUCCESS]'
            }.get(level, '[INFO]')
            print(f"{prefix} {message}")

    def check_audio_datasets(self):
        """Validate audio datasets (ESC-50 and UrbanSound8K)."""
        self.log("Checking audio datasets...", 'info')
        audio_base = self.base_dir / 'datasets' / 'datasets audio'

        # Check ESC-50
        esc50_dir = audio_base / 'ESC-50-master' / 'ESC-50-master'
        esc50_csv = esc50_dir / 'meta' / 'esc50.csv'
        esc50_audio_dir = esc50_dir / 'audio'

        if esc50_csv.exists():
            try:
                with open(esc50_csv, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                    self.stats['esc50_metadata_rows'] = len(rows)
                    self.log(f"  ESC-50 metadata: {len(rows)} entries", 'success')
            except Exception as e:
                self.errors.append(f"ESC-50 metadata file corrupt: {e}")
                self.log(f"  ESC-50 metadata corrupt: {e}", 'error')
        else:
            self.errors.append(f"ESC-50 metadata not found: {esc50_csv}")
            self.log(f"  ESC-50 metadata missing", 'error')

        if esc50_audio_dir.exists():
            audio_files = list(esc50_audio_dir.glob('*.wav'))
            self.stats['esc50_audio_files'] = len(audio_files)
            self.log(f"  ESC-50 audio files: {len(audio_files)}", 'success')

            if len(audio_files) < 2000:
                self.warnings.append(f"ESC-50 has only {len(audio_files)} files (expected 2000)")
                self.log(f"  ESC-50 incomplete: {len(audio_files)}/2000 files", 'warning')
        else:
            self.errors.append(f"ESC-50 audio directory not found: {esc50_audio_dir}")
            self.log(f"  ESC-50 audio directory missing", 'error')

        # Check UrbanSound8K
        urbansound_csv = audio_base / 'urbansound8kdataset' / 'UrbanSound8K.csv'

        if urbansound_csv.exists():
            try:
                with open(urbansound_csv, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                    self.stats['urbansound_metadata_rows'] = len(rows)

                    # Count by fold
                    fold_counts = defaultdict(int)
                    class_counts = defaultdict(int)
                    for row in rows:
                        fold_counts[row.get('fold', 'unknown')] += 1
                        class_counts[row.get('class', 'unknown')] += 1

                    self.log(f"  UrbanSound8K metadata: {len(rows)} entries", 'success')
                    if self.verbose:
                        self.log(f"    Folds: {dict(fold_counts)}")
                        self.log(f"    Classes: {len(class_counts)}")
            except Exception as e:
                self.errors.append(f"UrbanSound8K metadata file corrupt: {e}")
                self.log(f"  UrbanSound8K metadata corrupt: {e}", 'error')
        else:
            self.warnings.append(f"UrbanSound8K metadata not found (but ZIP exists): {urbansound_csv}")
            self.log(f"  UrbanSound8K metadata missing (may need extraction)", 'warning')

        # Check for ZIP files
        esc50_zip = audio_base / 'ESC-50-master.zip'
        urbansound_zip = audio_base / 'urbansound8kdataset.zip'

        if esc50_zip.exists():
            self.log(f"  ESC-50 ZIP found: {esc50_zip.stat().st_size / 1024 / 1024:.1f} MB", 'info')

        if urbansound_zip.exists():
            self.log(f"  UrbanSound8K ZIP found: {urbansound_zip.stat().st_size / 1024 / 1024:.1f} MB", 'info')

    def check_thermal_datasets(self):
        """Validate thermal camera datasets."""
        self.log("Checking thermal camera datasets...", 'info')
        thermal_base = self.base_dir / 'datasets' / 'thermal camera dataset'

        # Check Trimodal Dataset
        trimodal_dir = thermal_base / 'trimodaldataset'

        # Check JSON metadata files
        for json_type in ['thermal', 'rgb', 'depth']:
            json_file = trimodal_dir / f'trimodal-{json_type}.json'
            if json_file.exists():
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        entries = len(data.get('images', [])) if isinstance(data, dict) else len(data)
                        self.stats[f'trimodal_{json_type}_entries'] = entries
                        self.log(f"  Trimodal {json_type} metadata: {entries} entries", 'success')
                except Exception as e:
                    self.errors.append(f"Trimodal {json_type} JSON corrupt: {e}")
                    self.log(f"  Trimodal {json_type} JSON corrupt: {e}", 'error')
            else:
                self.warnings.append(f"Trimodal {json_type} metadata not found: {json_file}")
                self.log(f"  Trimodal {json_type} metadata missing", 'warning')

        # Check TrimodalDataset structure
        dataset_dir = trimodal_dir / 'TrimodalDataset'
        if dataset_dir.exists():
            scenes = [d for d in dataset_dir.iterdir() if d.is_dir() and d.name.startswith('Scene')]
            self.stats['trimodal_scenes'] = len(scenes)
            self.log(f"  Trimodal scenes: {len(scenes)}", 'success')

            total_images = 0
            for scene in scenes:
                # Count images in each modality
                for modality in ['SyncT', 'SyncRGB', 'SyncD']:
                    modality_dir = scene / modality
                    if modality_dir.exists():
                        images = list(modality_dir.glob('*.png'))
                        total_images += len(images)
                        if self.verbose:
                            self.log(f"    {scene.name}/{modality}: {len(images)} images")

                # Check annotations
                annotations_file = scene / 'annotations.csv'
                if annotations_file.exists():
                    try:
                        with open(annotations_file, 'r', encoding='utf-8') as f:
                            reader = csv.reader(f)
                            rows = list(reader)
                            if self.verbose:
                                self.log(f"    {scene.name}/annotations.csv: {len(rows)} rows")
                    except Exception as e:
                        self.warnings.append(f"Scene {scene.name} annotations corrupt: {e}")

            self.stats['trimodal_total_images'] = total_images
            self.log(f"  Total thermal images: {total_images}", 'success')
        else:
            self.errors.append(f"TrimodalDataset directory not found: {dataset_dir}")
            self.log(f"  TrimodalDataset directory missing", 'error')

    def check_timeseries_datasets(self):
        """Validate time-series anomaly detection datasets."""
        self.log("Checking time-series datasets...", 'info')
        timeseries_base = self.base_dir / 'datasets' / 'time-series anomaly detection datasets'

        if timeseries_base.exists():
            subdirs = [d for d in timeseries_base.iterdir() if d.is_dir()]
            self.stats['timeseries_subdirs'] = len(subdirs)
            self.log(f"  Time-series dataset directories: {len(subdirs)}", 'success')

            if self.verbose:
                for subdir in subdirs:
                    files = list(subdir.glob('*'))
                    self.log(f"    {subdir.name}: {len(files)} files")
        else:
            self.warnings.append(f"Time-series dataset directory not found: {timeseries_base}")
            self.log(f"  Time-series datasets missing", 'warning')

    def validate_all(self):
        """Run all validation checks."""
        self.log("=" * 60, 'info')
        self.log("PREMONITOR DATASET VALIDATION REPORT", 'info')
        self.log("=" * 60, 'info')

        self.check_audio_datasets()
        self.check_thermal_datasets()
        self.check_timeseries_datasets()

        return self.generate_report()

    def generate_report(self):
        """Generate final validation report."""
        self.log("\n" + "=" * 60, 'info')
        self.log("VALIDATION SUMMARY", 'info')
        self.log("=" * 60, 'info')

        # Print statistics
        if self.stats:
            self.log("\nDataset Statistics:", 'info')
            for key, value in sorted(self.stats.items()):
                self.log(f"  {key}: {value}", 'info')

        # Print warnings
        if self.warnings:
            self.log(f"\nWarnings ({len(self.warnings)}):", 'warning')
            for warning in self.warnings:
                self.log(f"  - {warning}", 'warning')

        # Print errors
        if self.errors:
            self.log(f"\nErrors ({len(self.errors)}):", 'error')
            for error in self.errors:
                self.log(f"  - {error}", 'error')

        # Final status
        self.log("\n" + "=" * 60, 'info')
        if self.errors:
            self.log("VALIDATION FAILED - Critical datasets missing", 'error')
            self.log("=" * 60, 'info')
            return False
        elif self.warnings:
            self.log("VALIDATION PASSED WITH WARNINGS", 'warning')
            self.log("=" * 60, 'info')
            return True
        else:
            self.log("VALIDATION PASSED - All datasets OK", 'success')
            self.log("=" * 60, 'info')
            return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Validate Premonitor datasets',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        '--base-dir',
        default=None,
        help='Base directory of the project (default: auto-detect)'
    )

    args = parser.parse_args()

    # Determine base directory
    if args.base_dir:
        base_dir = Path(args.base_dir)
    else:
        # Assume script is in scripts/ subdirectory
        base_dir = Path(__file__).resolve().parent.parent

    if not base_dir.exists():
        print(f"[ERROR] Base directory not found: {base_dir}", file=sys.stderr)
        return 2

    # Run validation
    validator = DatasetValidator(base_dir, verbose=args.verbose)

    try:
        success = validator.validate_all()
        return 0 if success else 1
    except Exception as e:
        print(f"[ERROR] Validation script failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 2


if __name__ == '__main__':
    sys.exit(main())
