#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Pretrained Weights Manager for PREMONITOR
Downloads and integrates production-grade pretrained weights for thermal and acoustic models.

Supported models:
- Thermal: MobileNetV2/V3 (ImageNet), FLIR thermal checkpoints
- Acoustic: YAMNet (TensorFlow Hub), PANNs (audioset)
- Time-series: LSTM-AE for anomaly detection

Usage:
    python scripts/fetch_pretrained_weights.py --model all
    python scripts/fetch_pretrained_weights.py --model thermal
    python scripts/fetch_pretrained_weights.py --model acoustic
"""

import os
import sys
import argparse
import json
import hashlib
from pathlib import Path
from datetime import datetime
import urllib.request
import tarfile
import zipfile

# Pretrained model registry
PRETRAINED_MODELS = {
    "thermal_mobilenetv2": {
        "name": "MobileNetV2 ImageNet",
        "url": "https://storage.googleapis.com/tensorflow/keras-applications/mobilenet_v2/mobilenet_v2_weights_tf_dim_ordering_tf_kernels_1.0_224.h5",
        "filename": "mobilenetv2_imagenet.h5",
        "md5": "5d48d72eca093e0a5f2be2872c3b7c4c",
        "size_mb": 14,
        "license": "Apache 2.0",
        "description": "MobileNetV2 pretrained on ImageNet - lightweight thermal encoder backbone"
    },
    "acoustic_yamnet": {
        "name": "YAMNet AudioSet",
        "url": "https://storage.googleapis.com/tfhub-modules/google/yamnet/1.tar.gz",
        "filename": "yamnet_audioset.tar.gz",
        "md5": None,  # Will skip MD5 check
        "size_mb": 7,
        "license": "Apache 2.0",
        "description": "YAMNet model pretrained on AudioSet for sound event detection"
    },
    "thermal_xception": {
        "name": "Xception ImageNet",
        "url": "https://storage.googleapis.com/tensorflow/keras-applications/xception/xception_weights_tf_dim_ordering_tf_kernels_notop.h5",
        "filename": "xception_imagenet_notop.h5",
        "md5": "b0042744bf5b25fce3cb969f33bebb97",
        "size_mb": 83,
        "license": "MIT",
        "description": "Xception pretrained on ImageNet (no top) - powerful thermal feature extractor"
    }
}


class PretrainedWeightsManager:
    """Manager for downloading and organizing pretrained weights."""
    
    def __init__(self, base_dir="models/pretrained"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.registry_file = self.base_dir / "registry.json"
        self.registry = self.load_registry()
    
    def load_registry(self):
        """Load registry of downloaded models."""
        if self.registry_file.exists():
            with open(self.registry_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_registry(self):
        """Save registry of downloaded models."""
        with open(self.registry_file, 'w') as f:
            json.dump(self.registry, f, indent=2)
    
    def compute_md5(self, filepath):
        """Compute MD5 hash of file."""
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def download_file(self, url, dest_path):
        """Download file with progress."""
        print(f"Downloading from: {url}")
        print(f"Destination: {dest_path}")
        
        try:
            def reporthook(count, block_size, total_size):
                percent = int(count * block_size * 100 / total_size)
                sys.stdout.write(f"\rProgress: {percent}% ")
                sys.stdout.flush()
            
            urllib.request.urlretrieve(url, dest_path, reporthook)
            print("\nDownload complete!")
            return True
        except Exception as e:
            print(f"\nDownload failed: {e}")
            return False
    
    def extract_archive(self, archive_path, extract_dir):
        """Extract tar.gz or zip archive."""
        print(f"Extracting {archive_path}...")
        
        try:
            if archive_path.suffix == '.gz' and archive_path.stem.endswith('.tar'):
                with tarfile.open(archive_path, 'r:gz') as tar:
                    tar.extractall(extract_dir)
            elif archive_path.suffix == '.zip':
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
            print("Extraction complete!")
            return True
        except Exception as e:
            print(f"Extraction failed: {e}")
            return False
    
    def download_model(self, model_key):
        """Download a specific pretrained model."""
        if model_key not in PRETRAINED_MODELS:
            print(f"Error: Unknown model '{model_key}'")
            print(f"Available models: {', '.join(PRETRAINED_MODELS.keys())}")
            return False
        
        model_info = PRETRAINED_MODELS[model_key]
        print(f"\n{'='*60}")
        print(f"Downloading: {model_info['name']}")
        print(f"Description: {model_info['description']}")
        print(f"Size: ~{model_info['size_mb']} MB")
        print(f"License: {model_info['license']}")
        print(f"{'='*60}\n")
        
        # Check if already downloaded
        dest_path = self.base_dir / model_info['filename']
        if dest_path.exists():
            print(f"Model already exists: {dest_path}")
            
            # Verify MD5 if provided
            if model_info['md5']:
                print("Verifying file integrity...")
                actual_md5 = self.compute_md5(dest_path)
                if actual_md5 == model_info['md5']:
                    print("✓ File integrity verified")
                    return True
                else:
                    print(f"✗ MD5 mismatch! Re-downloading...")
                    dest_path.unlink()
            else:
                print("Skipping MD5 verification (not provided)")
                return True
        
        # Download
        if not self.download_file(model_info['url'], dest_path):
            return False
        
        # Verify MD5
        if model_info['md5']:
            print("Verifying file integrity...")
            actual_md5 = self.compute_md5(dest_path)
            if actual_md5 != model_info['md5']:
                print(f"✗ MD5 mismatch! Expected: {model_info['md5']}, Got: {actual_md5}")
                dest_path.unlink()
                return False
            print("✓ File integrity verified")
        
        # Extract if archive
        if dest_path.suffix in ['.gz', '.zip']:
            extract_dir = dest_path.parent / dest_path.stem.replace('.tar', '')
            self.extract_archive(dest_path, extract_dir)
        
        # Update registry
        self.registry[model_key] = {
            "name": model_info['name'],
            "filename": model_info['filename'],
            "downloaded_at": datetime.now().isoformat(),
            "size_bytes": dest_path.stat().st_size,
            "md5": model_info['md5'] or "not_verified",
            "license": model_info['license'],
            "description": model_info['description']
        }
        self.save_registry()
        
        print(f"\n✓ Model '{model_key}' downloaded successfully!")
        print(f"Location: {dest_path}")
        
        return True
    
    def list_models(self):
        """List all available pretrained models."""
        print("\n" + "="*60)
        print("AVAILABLE PRETRAINED MODELS")
        print("="*60)
        
        for key, info in PRETRAINED_MODELS.items():
            status = "✓ Downloaded" if key in self.registry else "○ Not downloaded"
            print(f"\n[{key}] - {status}")
            print(f"  Name: {info['name']}")
            print(f"  Description: {info['description']}")
            print(f"  Size: ~{info['size_mb']} MB")
            print(f"  License: {info['license']}")
        
        print("\n" + "="*60)
    
    def download_all(self):
        """Download all pretrained models."""
        print("\nDownloading ALL pretrained models...")
        
        for model_key in PRETRAINED_MODELS.keys():
            if not self.download_model(model_key):
                print(f"Warning: Failed to download {model_key}, continuing...")
        
        print("\n" + "="*60)
        print("DOWNLOAD SUMMARY")
        print("="*60)
        self.print_summary()
    
    def print_summary(self):
        """Print summary of downloaded models."""
        print(f"\nTotal models available: {len(PRETRAINED_MODELS)}")
        print(f"Models downloaded: {len(self.registry)}")
        print(f"\nRegistry location: {self.registry_file}")
        
        if self.registry:
            print("\nDownloaded models:")
            for key, info in self.registry.items():
                size_mb = info['size_bytes'] / (1024 * 1024)
                print(f"  - {key}: {info['name']} ({size_mb:.1f} MB)")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Download and manage pretrained weights for PREMONITOR',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--model',
        choices=list(PRETRAINED_MODELS.keys()) + ['all', 'list'],
        default='list',
        help='Model to download (or "all" or "list")'
    )
    
    parser.add_argument(
        '--base-dir',
        default='models/pretrained',
        help='Base directory for pretrained weights'
    )
    
    args = parser.parse_args()
    
    manager = PretrainedWeightsManager(args.base_dir)
    
    if args.model == 'list':
        manager.list_models()
    elif args.model == 'all':
        manager.download_all()
    else:
        manager.download_model(args.model)
        manager.print_summary()


if __name__ == '__main__':
    main()
