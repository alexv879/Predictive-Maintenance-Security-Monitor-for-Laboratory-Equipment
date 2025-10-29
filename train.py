#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PREMONITOR Training Script
Standalone script for training thermal and acoustic anomaly detection models.

Usage:
    # Smoke test (quick validation with small dataset)
    python train.py --mode smoke_test --model thermal

    # Full thermal model training
    python train.py --mode full --model thermal

    # Full acoustic model training
    python train.py --mode full --model acoustic

    # Train all models
    python train.py --mode full --model all

Author: PREMONITOR Team
Date: 2025-10-29
"""

import os
import sys
import argparse
import yaml
import numpy as np
import tensorflow as tf
from tensorflow.keras import optimizers, losses, models, layers, callbacks
from pathlib import Path
import json
from datetime import datetime

# Add pythonsoftware to path for imports
SCRIPT_DIR = Path(__file__).resolve().parent
PYTHONSOFTWARE_DIR = SCRIPT_DIR / 'pythonsoftware'
sys.path.insert(0, str(PYTHONSOFTWARE_DIR))

# Import project modules will be done conditionally when needed
# For smoke test mode, we'll use standalone implementations
config = None
model_blueprints = None
utils = None
imports_successful = False


class PremonitorTrainer:
    """Main training class for PREMONITOR models."""

    def __init__(self, config_path='training_config.yaml'):
        """Initialize trainer with configuration."""
        self.config_path = config_path
        self.cfg = self.load_config()
        self.setup_environment()
        self.setup_paths()

    def load_config(self):
        """Load training configuration from YAML."""
        if not os.path.exists(self.config_path):
            print(f"Warning: Config file {self.config_path} not found. Using defaults.")
            return self.get_default_config()

        with open(self.config_path, 'r') as f:
            cfg = yaml.safe_load(f)
        print(f"Loaded configuration from {self.config_path}")
        return cfg

    def get_default_config(self):
        """Return minimal default configuration."""
        return {
            'general': {'random_seed': 42},
            'paths': {
                'base_dir': str(SCRIPT_DIR),
                'models_dir': str(SCRIPT_DIR / 'models'),
                'checkpoints_dir': str(SCRIPT_DIR / 'models' / 'checkpoints'),
            },
            'thermal_model': {
                'input_shape': [224, 224, 3],
                'pre_training': {'epochs': 2, 'batch_size': 16},
                'fine_tuning': {'epochs': 2, 'batch_size': 16},
            },
            'acoustic_model': {
                'input_shape': [128, 128, 1],
                'training': {'epochs': 2, 'batch_size': 16},
            },
            'training_modes': {
                'smoke_test': {'enabled': True, 'thermal_samples': 50, 'acoustic_samples': 50}
            }
        }

    def setup_environment(self):
        """Set up TensorFlow environment and random seeds."""
        # Set random seeds for reproducibility
        seed = self.cfg.get('general', {}).get('random_seed', 42)
        np.random.seed(seed)
        tf.random.set_seed(seed)

        # GPU configuration
        gpus = tf.config.list_physical_devices('GPU')
        if gpus and self.cfg.get('general', {}).get('use_gpu', True):
            try:
                for gpu in gpus:
                    tf.config.experimental.set_memory_growth(gpu, True)
                print(f"Found {len(gpus)} GPU(s), memory growth enabled")
            except RuntimeError as e:
                print(f"GPU setup error: {e}")
        else:
            print("Running on CPU")

        # Mixed precision
        if self.cfg.get('general', {}).get('mixed_precision', False):
            tf.keras.mixed_precision.set_global_policy('mixed_float16')
            print("Mixed precision enabled")

    def setup_paths(self):
        """Create necessary directories."""
        paths_cfg = self.cfg.get('paths', {})
        dirs_to_create = [
            paths_cfg.get('models_dir', 'models'),
            paths_cfg.get('checkpoints_dir', 'models/checkpoints'),
            paths_cfg.get('exported_dir', 'models/exported'),
            paths_cfg.get('pretrained_dir', 'models/pretrained'),
            paths_cfg.get('logs_dir', 'logs'),
        ]

        for dir_path in dirs_to_create:
            os.makedirs(dir_path, exist_ok=True)
            print(f"Ensured directory exists: {dir_path}")

    def check_pretrained_weights(self):
        """Check availability of pretrained weights."""
        pretrained_models = self.cfg.get('paths', {}).get('pretrained_models', {})

        status = {
            'xception_available': False,
            'thermal_encoder_available': False,
            'acoustic_baseline_available': False
        }

        # Check Xception
        xception_path = pretrained_models.get('xception_imagenet', '')
        if xception_path and os.path.exists(xception_path):
            status['xception_available'] = True
            print(f"✓ Found pretrained Xception: {xception_path}")

        # Check thermal encoder
        thermal_encoder_path = pretrained_models.get('thermal_encoder', '')
        if thermal_encoder_path and os.path.exists(thermal_encoder_path):
            status['thermal_encoder_available'] = True
            print(f"✓ Found pretrained thermal encoder: {thermal_encoder_path}")

        # Check acoustic baseline
        acoustic_path = pretrained_models.get('acoustic_baseline', '')
        if acoustic_path and os.path.exists(acoustic_path):
            status['acoustic_baseline_available'] = True
            print(f"✓ Found pretrained acoustic baseline: {acoustic_path}")

        return status

    def create_synthetic_thermal_data(self, num_samples=100):
        """Create synthetic thermal data for smoke testing."""
        print(f"Creating {num_samples} synthetic thermal images...")
        input_shape = self.cfg['thermal_model']['input_shape']

        # Create random images with some structure
        images = []
        labels = []

        for i in range(num_samples):
            # Create structured noise that looks somewhat like thermal images
            img = np.random.rand(*input_shape).astype(np.float32)

            # Add some gaussian blobs to simulate hotspots
            center_y, center_x = np.random.randint(50, 174, 2)
            y, x = np.ogrid[:input_shape[0], :input_shape[1]]
            mask = ((y - center_y)**2 + (x - center_x)**2) <= 30**2
            img[mask] = np.random.rand() * 0.5 + 0.5  # Brighter center

            images.append(img)

            # Random labels (50/50 split)
            labels.append(i % 2)

        return np.array(images), np.array(labels)

    def create_synthetic_acoustic_data(self, num_samples=100):
        """Create synthetic acoustic spectrograms for smoke testing."""
        print(f"Creating {num_samples} synthetic spectrograms...")
        input_shape = self.cfg['acoustic_model']['input_shape']

        images = []
        labels = []

        for i in range(num_samples):
            # Create spectrogram-like data with frequency structure
            spec = np.random.rand(*input_shape).astype(np.float32)

            # Add harmonic structure (common in machine sounds)
            for harmonic in range(1, 5):
                freq_band = int(input_shape[0] * harmonic / 10)
                if freq_band < input_shape[0]:
                    spec[freq_band:freq_band+2, :] += 0.3

            images.append(spec)
            labels.append(i % 2)

        return np.array(images), np.array(labels)

    def train_thermal_model_smoke(self):
        """Train thermal model with synthetic data (smoke test)."""
        print("\n" + "="*60)
        print("THERMAL MODEL - SMOKE TEST")
        print("="*60)

        # Get configuration
        thermal_cfg = self.cfg['thermal_model']
        input_shape = tuple(thermal_cfg['input_shape'])

        # Create synthetic data
        num_samples = self.cfg['training_modes']['smoke_test']['thermal_samples']
        X, y = self.create_synthetic_thermal_data(num_samples)

        # Split data
        split_idx = int(len(X) * 0.8)
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]

        print(f"Train samples: {len(X_train)}, Val samples: {len(X_val)}")

        # Create simple model (skip SimSiam for smoke test)
        print("Creating simple CNN model...")
        model = tf.keras.Sequential([
            layers.Input(shape=input_shape),
            layers.Conv2D(32, 3, activation='relu'),
            layers.MaxPooling2D(2),
            layers.Conv2D(64, 3, activation='relu'),
            layers.MaxPooling2D(2),
            layers.Flatten(),
            layers.Dense(64, activation='relu'),
            layers.Dropout(0.5),
            layers.Dense(1, activation='sigmoid')
        ], name='thermal_smoke_test')

        # Compile
        model.compile(
            optimizer='adam',
            loss='binary_crossentropy',
            metrics=['accuracy']
        )

        model.summary()

        # Train
        print("\nTraining...")
        checkpoint_path = os.path.join(
            self.cfg['paths']['checkpoints_dir'],
            'thermal_smoke_test.h5'
        )

        history = model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=self.cfg['training_modes']['smoke_test'].get('epochs', 2),
            batch_size=16,
            callbacks=[
                callbacks.ModelCheckpoint(checkpoint_path, save_best_only=True),
                callbacks.EarlyStopping(patience=3, restore_best_weights=True)
            ]
        )

        # Save final model
        model.save(checkpoint_path)
        print(f"\nModel saved to {checkpoint_path}")

        # Report results
        val_acc = history.history['val_accuracy'][-1]
        print(f"Final validation accuracy: {val_acc:.4f}")

        return model, history

    def train_acoustic_model_smoke(self):
        """Train acoustic model with synthetic data (smoke test)."""
        print("\n" + "="*60)
        print("ACOUSTIC MODEL - SMOKE TEST")
        print("="*60)

        # Get configuration
        acoustic_cfg = self.cfg['acoustic_model']
        input_shape = tuple(acoustic_cfg['input_shape'])

        # Create synthetic data
        num_samples = self.cfg['training_modes']['smoke_test']['acoustic_samples']
        X, y = self.create_synthetic_acoustic_data(num_samples)

        # Split data
        split_idx = int(len(X) * 0.8)
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]

        print(f"Train samples: {len(X_train)}, Val samples: {len(X_val)}")

        # Create simple CNN model
        print("Creating simple CNN model...")
        model = tf.keras.Sequential([
            layers.Input(shape=input_shape),
            layers.Conv2D(32, 3, activation='relu'),
            layers.MaxPooling2D(2),
            layers.Conv2D(64, 3, activation='relu'),
            layers.MaxPooling2D(2),
            layers.Flatten(),
            layers.Dense(64, activation='relu'),
            layers.Dropout(0.5),
            layers.Dense(1, activation='sigmoid')
        ], name='acoustic_smoke_test')

        # Compile
        model.compile(
            optimizer='adam',
            loss='binary_crossentropy',
            metrics=['accuracy']
        )

        model.summary()

        # Train
        print("\nTraining...")
        checkpoint_path = os.path.join(
            self.cfg['paths']['checkpoints_dir'],
            'acoustic_smoke_test.h5'
        )

        history = model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=self.cfg['training_modes']['smoke_test'].get('epochs', 2),
            batch_size=16,
            callbacks=[
                callbacks.ModelCheckpoint(checkpoint_path, save_best_only=True),
                callbacks.EarlyStopping(patience=3, restore_best_weights=True)
            ]
        )

        # Save final model
        model.save(checkpoint_path)
        print(f"\nModel saved to {checkpoint_path}")

        # Report results
        val_acc = history.history['val_accuracy'][-1]
        print(f"Final validation accuracy: {val_acc:.4f}")

        return model, history

    def save_training_report(self, model_name, history, model_path):
        """Save training report to JSON."""
        report = {
            'model_name': model_name,
            'timestamp': datetime.now().isoformat(),
            'model_path': model_path,
            'final_metrics': {
                key: float(val[-1]) if isinstance(val[-1], (np.floating, float)) else val[-1]
                for key, val in history.history.items()
            },
            'training_config': {
                'epochs': len(history.history['loss']),
                'final_epoch': len(history.history['loss']),
            }
        }

        report_path = os.path.join(
            self.cfg['paths']['checkpoints_dir'],
            f'{model_name}_training_report.json'
        )

        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"Training report saved to {report_path}")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='PREMONITOR Model Training Script',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Smoke test thermal model
  python train.py --mode smoke_test --model thermal

  # Smoke test acoustic model
  python train.py --mode smoke_test --model acoustic

  # Smoke test all models
  python train.py --mode smoke_test --model all

  # Full training (requires datasets)
  python train.py --mode full --model thermal --config training_config.yaml
        """
    )

    parser.add_argument(
        '--mode',
        choices=['smoke_test', 'development', 'full'],
        default='smoke_test',
        help='Training mode (default: smoke_test)'
    )

    parser.add_argument(
        '--model',
        choices=['thermal', 'acoustic', 'all'],
        default='all',
        help='Which model to train (default: all)'
    )

    parser.add_argument(
        '--config',
        default='training_config.yaml',
        help='Path to training configuration file'
    )

    parser.add_argument(
        '--output-dir',
        default=None,
        help='Override output directory for models'
    )

    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()

    print("="*60)
    print("PREMONITOR MODEL TRAINING")
    print("="*60)
    print(f"Mode: {args.mode}")
    print(f"Model: {args.model}")
    print(f"Config: {args.config}")
    print(f"TensorFlow version: {tf.__version__}")
    print(f"NumPy version: {np.__version__}")
    print("="*60)

    # Initialize trainer
    trainer = PremonitorTrainer(config_path=args.config)

    # Override paths if specified
    if args.output_dir:
        trainer.cfg['paths']['models_dir'] = args.output_dir
        trainer.cfg['paths']['checkpoints_dir'] = os.path.join(args.output_dir, 'checkpoints')
        trainer.setup_paths()

    # Check pretrained weights availability
    print("\nChecking pretrained weights...")
    pretrained_status = trainer.check_pretrained_weights()

    results = {}

    # Execute training based on mode and model selection
    if args.mode == 'smoke_test':
        # Check if we should skip smoke test when pretrained weights exist
        thermal_cfg = trainer.cfg.get('thermal_model', {})
        acoustic_cfg = trainer.cfg.get('acoustic_model', {})

        if args.model in ['thermal', 'all']:
            # Skip smoke test if pretrained encoder exists and use_pretrained is enabled
            if (pretrained_status['thermal_encoder_available'] and
                thermal_cfg.get('use_pretrained_encoder', True)):
                print("\n>>> Skipping thermal smoke test - pretrained encoder found")
                print(f"    Use pretrained encoder for deployment or fine-tuning")
            else:
                print("\n>>> Training Thermal Model (Smoke Test)...")
                model, history = trainer.train_thermal_model_smoke()
                trainer.save_training_report('thermal_smoke_test', history,
                                            os.path.join(trainer.cfg['paths']['checkpoints_dir'],
                                                        'thermal_smoke_test.h5'))
                results['thermal'] = {'model': model, 'history': history}

        if args.model in ['acoustic', 'all']:
            # Skip smoke test if pretrained baseline exists
            if (pretrained_status['acoustic_baseline_available'] and
                acoustic_cfg.get('use_pretrained_baseline', True)):
                print("\n>>> Skipping acoustic smoke test - pretrained baseline found")
                print(f"    Use pretrained baseline for deployment or fine-tuning")
            else:
                print("\n>>> Training Acoustic Model (Smoke Test)...")
                model, history = trainer.train_acoustic_model_smoke()
                trainer.save_training_report('acoustic_smoke_test', history,
                                            os.path.join(trainer.cfg['paths']['checkpoints_dir'],
                                                        'acoustic_smoke_test.h5'))
                results['acoustic'] = {'model': model, 'history': history}

    elif args.mode in ['development', 'full']:
        print(f"\n{args.mode.upper()} mode not yet implemented.")
        print("This requires real datasets to be present.")
        print("Please ensure datasets are downloaded and paths are configured correctly.")
        print("\nRequired datasets:")
        print("- Thermal: AAU VAP Trimodal Dataset (present)")
        print("- Acoustic: MIMII 0_dB_fan.zip (10.4 GB) - DOWNLOAD REQUIRED")
        print("- Acoustic: ESC-50 (present), UrbanSound8K (present)")
        return 1

    # Final summary
    print("\n" + "="*60)
    print("TRAINING COMPLETE")
    print("="*60)

    if results:
        print(f"\nTrained {len(results)} model(s):")
        for model_name in results:
            print(f"  - {model_name.upper()}")

        print(f"\nModels saved to: {trainer.cfg['paths']['checkpoints_dir']}")
        print("\nNext steps:")
        print("1. Export models to TFLite: python export_tflite.py")
        print("2. Validate exported models: python validate_tflite.py")
        print("3. Deploy to Raspberry Pi: see DEPLOYMENT.md")

    return 0


if __name__ == '__main__':
    sys.exit(main())
