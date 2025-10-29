#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Pretrained Weight Downloader for PREMONITOR
Downloads and prepares publicly available pretrained models

Usage:
    python scripts/download_pretrained_weights.py --all
    python scripts/download_pretrained_weights.py --thermal
    python scripts/download_pretrained_weights.py --acoustic
"""

import os
import sys
import argparse
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

PRETRAINED_DIR = PROJECT_ROOT / 'models' / 'pretrained'


def download_xception_weights():
    """Download Xception ImageNet weights via Keras."""
    print("\n" + "="*60)
    print("DOWNLOADING: Xception (ImageNet) Backbone")
    print("="*60)

    try:
        import tensorflow as tf
        from tensorflow.keras.applications import Xception

        print("Loading Xception with ImageNet weights...")
        model = Xception(weights='imagenet', include_top=False,
                        input_shape=(224, 224, 3))

        # Save to pretrained directory
        output_dir = PRETRAINED_DIR / 'thermal'
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / 'xception_notop_imagenet.h5'

        model.save(output_path)
        print(f"✓ Saved to: {output_path}")

        # Save metadata
        metadata = {
            "model_name": "Xception",
            "source": "Keras Applications",
            "weights": "ImageNet",
            "architecture": "Xception",
            "input_shape": [224, 224, 3],
            "license": "Apache 2.0",
            "download_date": datetime.now().isoformat(),
            "url": "https://storage.googleapis.com/tensorflow/keras-applications/xception/",
            "paper": "Xception: Deep Learning with Depthwise Separable Convolutions (Chollet, 2017)",
            "use_case": "Thermal anomaly detection backbone"
        }

        metadata_path = output_dir / 'xception_metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        print(f"✓ Metadata saved to: {metadata_path}")
        print(f"✓ Model size: {output_path.stat().st_size / 1024 / 1024:.1f} MB")

        return True

    except Exception as e:
        print(f"✗ Error downloading Xception: {e}")
        return False


def download_yamnet():
    """Download YAMNet from TensorFlow Hub."""
    print("\n" + "="*60)
    print("DOWNLOADING: YAMNet (AudioSet)")
    print("="*60)

    try:
        import tensorflow as tf
        import tensorflow_hub as hub

        print("Loading YAMNet from TensorFlow Hub...")
        model = hub.load('https://tfhub.dev/google/yamnet/1')

        print("✓ YAMNet loaded successfully")
        print("✓ Model cached in TensorFlow Hub cache directory")
        print("  (usually ~/.cache/tfhub_modules/ or %LOCALAPPDATA%\\TFHub)")

        # Save metadata
        output_dir = PRETRAINED_DIR / 'acoustic'
        output_dir.mkdir(parents=True, exist_ok=True)

        metadata = {
            "model_name": "YAMNet",
            "source": "TensorFlow Hub",
            "weights": "AudioSet",
            "architecture": "MobileNet-v1",
            "input_type": "16kHz mono audio waveform",
            "output_classes": 521,
            "license": "Apache 2.0",
            "download_date": datetime.now().isoformat(),
            "url": "https://tfhub.dev/google/yamnet/1",
            "paper": "Transfer Learning for Audio Classification (Google, 2020)",
            "use_case": "Audio feature extraction for anomaly detection"
        }

        metadata_path = output_dir / 'yamnet_metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        print(f"✓ Metadata saved to: {metadata_path}")

        # Create a note file
        note_path = output_dir / 'yamnet_usage.txt'
        with open(note_path, 'w') as f:
            f.write("YAMNet Usage Instructions\n")
            f.write("="*60 + "\n\n")
            f.write("YAMNet is loaded from TensorFlow Hub:\n\n")
            f.write("  import tensorflow_hub as hub\n")
            f.write("  model = hub.load('https://tfhub.dev/google/yamnet/1')\n\n")
            f.write("Input: Raw audio waveform at 16kHz\n")
            f.write("Output: 521-class AudioSet predictions\n\n")
            f.write("For PREMONITOR, use YAMNet as feature extractor:\n")
            f.write("  embeddings = model(audio_waveform)[1]  # Shape: (N, 1024)\n")

        print(f"✓ Usage instructions saved to: {note_path}")

        return True

    except ImportError:
        print("✗ Error: tensorflow_hub not installed")
        print("  Install with: pip install tensorflow-hub")
        return False
    except Exception as e:
        print(f"✗ Error downloading YAMNet: {e}")
        return False


def create_lstm_autoencoder_template():
    """Create LSTM autoencoder template (not pretrained, just architecture)."""
    print("\n" + "="*60)
    print("CREATING: LSTM Autoencoder Template")
    print("="*60)

    try:
        import tensorflow as tf
        from tensorflow.keras import layers, models

        # Create basic LSTM autoencoder architecture
        timesteps = 50
        n_features = 1

        model = models.Sequential([
            layers.Input(shape=(timesteps, n_features)),
            layers.LSTM(32, activation='relu', return_sequences=True),
            layers.LSTM(16, activation='relu', return_sequences=False),
            layers.RepeatVector(timesteps),
            layers.LSTM(16, activation='relu', return_sequences=True),
            layers.LSTM(32, activation='relu', return_sequences=True),
            layers.TimeDistributed(layers.Dense(n_features))
        ], name='lstm_autoencoder')

        output_dir = PRETRAINED_DIR / 'timeseries'
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / 'lstm_autoencoder_template.h5'

        model.save(output_path)
        print(f"✓ Template saved to: {output_path}")

        # Save metadata
        metadata = {
            "model_name": "LSTM Autoencoder",
            "source": "PREMONITOR (local)",
            "weights": "Random initialization (not pretrained)",
            "architecture": "LSTM Encoder-Decoder",
            "input_shape": [timesteps, n_features],
            "architecture_paper": "LSTM-based Autoencoder for Anomaly Detection (Reis & Serôdio)",
            "use_case": "Time-series anomaly detection (gas sensors, vibration)",
            "note": "This is an untrained template. Train on your specific time-series data.",
            "created_date": datetime.now().isoformat()
        }

        metadata_path = output_dir / 'lstm_metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        print(f"✓ Metadata saved to: {metadata_path}")
        print("⚠ Note: This is an untrained template, not pretrained weights")

        return True

    except Exception as e:
        print(f"✗ Error creating LSTM template: {e}")
        return False


def check_existing_models():
    """Check which models are already downloaded."""
    print("\n" + "="*60)
    print("CHECKING EXISTING MODELS")
    print("="*60)

    models_status = {
        'Xception (Thermal)': PRETRAINED_DIR / 'thermal' / 'xception_notop_imagenet.h5',
        'YAMNet (Acoustic)': PRETRAINED_DIR / 'acoustic' / 'yamnet_metadata.json',
        'LSTM Template (Time-series)': PRETRAINED_DIR / 'timeseries' / 'lstm_autoencoder_template.h5'
    }

    for name, path in models_status.items():
        exists = path.exists()
        status = "✓ Present" if exists else "✗ Missing"
        print(f"  {name}: {status}")
        if exists and path.suffix in ['.h5', '.pth']:
            size_mb = path.stat().st_size / 1024 / 1024
            print(f"    Size: {size_mb:.1f} MB")

    return models_status


def create_mimii_instructions():
    """Create instructions for MIMII dataset download (manual)."""
    print("\n" + "="*60)
    print("MIMII DATASET INSTRUCTIONS")
    print("="*60)

    output_dir = PRETRAINED_DIR / 'acoustic'
    output_dir.mkdir(parents=True, exist_ok=True)

    instructions_path = output_dir / 'MIMII_DOWNLOAD_INSTRUCTIONS.txt'

    instructions = """MIMII Dataset Download Instructions
=====================================

The MIMII dataset is required for acoustic anomaly detection training.
Due to its large size (10.4 GB for 0_dB_fan), it must be downloaded manually.

Dataset Information:
- Name: MIMII Dataset (Malfunctioning Industrial Machine Investigation)
- Size: 10.4 GB (0_dB_fan baseline recommended)
- License: CC BY 4.0
- Use: Machine sound anomaly detection

Download Steps:
1. Visit: https://zenodo.org/record/3384388
2. Scroll to "Files" section
3. Download: "0_dB_fan.zip" (10.4 GB)
4. Extract to: datasets/Mimii/0_dB_fan/
5. Verify structure:
   datasets/Mimii/0_dB_fan/
   ├── train/
   │   └── normal/
   └── test/
       ├── normal/
       └── abnormal/

Alternative (if full dataset unavailable):
- Train with synthetic data using: python train.py --mode smoke_test --model acoustic
- Use ESC-50 and UrbanSound8K for environmental sound robustness

Citation:
Purohit, H., Tanabe, R., Ichige, K., Endo, T., Nikaido, Y., Suefusa, K., & Kawaguchi, Y. (2019).
"MIMII Dataset: Sound Dataset for Malfunctioning Industrial Machine Investigation and Inspection."
DCASE2020 Challenge.

License: CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/)
Commercial use: Allowed with attribution
"""

    with open(instructions_path, 'w') as f:
        f.write(instructions)

    print(f"✓ Instructions saved to: {instructions_path}")
    print("\n⚠ MIMII dataset (10.4 GB) must be downloaded manually")
    print("  See instructions above for download link")

    return True


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Download pretrained weights for PREMONITOR',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Download all available pretrained models'
    )

    parser.add_argument(
        '--thermal',
        action='store_true',
        help='Download thermal model weights (Xception)'
    )

    parser.add_argument(
        '--acoustic',
        action='store_true',
        help='Download acoustic model weights (YAMNet)'
    )

    parser.add_argument(
        '--timeseries',
        action='store_true',
        help='Create LSTM autoencoder template'
    )

    parser.add_argument(
        '--check',
        action='store_true',
        help='Check which models are already downloaded'
    )

    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()

    print("="*60)
    print("PREMONITOR - Pretrained Weight Downloader")
    print("="*60)
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Pretrained directory: {PRETRAINED_DIR}")

    # Create base directory
    PRETRAINED_DIR.mkdir(parents=True, exist_ok=True)

    if args.check or (not args.all and not args.thermal and not args.acoustic and not args.timeseries):
        check_existing_models()
        if not args.all and not args.thermal and not args.acoustic and not args.timeseries:
            print("\nUse --all to download all models, or --thermal/--acoustic/--timeseries for specific models")
            return 0

    results = []

    # Download models based on arguments
    if args.all or args.thermal:
        results.append(('Xception', download_xception_weights()))

    if args.all or args.acoustic:
        results.append(('YAMNet', download_yamnet()))
        results.append(('MIMII Instructions', create_mimii_instructions()))

    if args.all or args.timeseries:
        results.append(('LSTM Template', create_lstm_autoencoder_template()))

    # Summary
    print("\n" + "="*60)
    print("DOWNLOAD SUMMARY")
    print("="*60)

    for name, success in results:
        status = "✓ SUCCESS" if success else "✗ FAILED"
        print(f"  {name}: {status}")

    all_success = all(success for _, success in results)

    if all_success:
        print("\n✓ All downloads completed successfully")
        print("\nNext steps:")
        print("  1. Review: models/pretrained/PRETRAINED_MODELS.md")
        print("  2. Configure: training_config.yaml")
        print("  3. Train: python train.py --mode full --model all")
        return 0
    else:
        print("\n⚠ Some downloads failed - check errors above")
        return 1


if __name__ == '__main__':
    sys.exit(main())
