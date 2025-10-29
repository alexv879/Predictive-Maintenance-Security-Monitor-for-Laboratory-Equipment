#!/usr/bin/env python
"""
PREMONITOR TFLite Export Script
Converts trained Keras models to TensorFlow Lite with quantization

Usage:
    python export_tflite.py --model models/checkpoints/thermal_smoke_test.h5
    python export_tflite.py --model thermal --quantize all
"""

import os
import argparse
import numpy as np
import tensorflow as tf
from pathlib import Path
import json

def representative_dataset_generator(input_shape, num_samples=100, use_real_data=False,
                                    dataset_path=None):
    """
    Generate representative dataset for INT8 quantization calibration.

    Args:
        input_shape: Model input shape (H, W, C)
        num_samples: Number of calibration samples
        use_real_data: If True and dataset_path provided, use real samples
        dataset_path: Path to dataset for real calibration data

    Yields:
        Single-sample batches for calibration
    """
    if use_real_data and dataset_path:
        try:
            # Try to load real samples from dataset
            import glob
            samples = []

            if 'thermal' in str(dataset_path).lower():
                # Load thermal images
                image_files = glob.glob(str(dataset_path) + '/**/*.png', recursive=True)
                image_files = image_files[:num_samples]

                for img_file in image_files:
                    try:
                        from PIL import Image
                        img = Image.open(img_file).resize((input_shape[0], input_shape[1]))
                        img_array = np.array(img).astype(np.float32) / 255.0

                        # Ensure correct shape
                        if len(img_array.shape) == 2:
                            img_array = np.stack([img_array]*3, axis=-1)
                        elif img_array.shape[-1] != input_shape[-1]:
                            img_array = img_array[:, :, :input_shape[-1]]

                        yield [np.expand_dims(img_array, axis=0)]
                    except Exception as e:
                        print(f"Warning: Failed to load {img_file}: {e}")

            elif 'acoustic' in str(dataset_path).lower():
                # Load acoustic spectrograms or generate from audio
                audio_files = glob.glob(str(dataset_path) + '/**/*.wav', recursive=True)
                audio_files = audio_files[:num_samples]

                for _ in audio_files:
                    # For now, use synthetic spectrograms
                    # In production, generate mel-spectrograms from audio files
                    data = np.random.rand(1, *input_shape).astype(np.float32)
                    yield [data]

            print(f"  Using real calibration data from {dataset_path}")
            return

        except Exception as e:
            print(f"  Warning: Could not load real calibration data: {e}")
            print(f"  Falling back to synthetic calibration data")

    # Fallback to synthetic data
    print(f"  Using synthetic calibration data ({num_samples} samples)")
    for _ in range(num_samples):
        data = np.random.rand(1, *input_shape).astype(np.float32)
        yield [data]

def export_float32(model, output_path):
    """Export model to float32 TFLite."""
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    tflite_model = converter.convert()

    with open(output_path, 'wb') as f:
        f.write(tflite_model)

    size_mb = len(tflite_model) / (1024 * 1024)
    print(f"  Float32 model: {size_mb:.2f} MB -> {output_path}")
    return size_mb

def export_dynamic_range(model, output_path):
    """Export model with dynamic range quantization."""
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    tflite_model = converter.convert()

    with open(output_path, 'wb') as f:
        f.write(tflite_model)

    size_mb = len(tflite_model) / (1024 * 1024)
    print(f"  Dynamic range model: {size_mb:.2f} MB -> {output_path}")
    return size_mb

def export_int8(model, input_shape, output_path, num_calibration=100,
               use_real_data=False, dataset_path=None):
    """Export model with full INT8 quantization."""
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.representative_dataset = lambda: representative_dataset_generator(
        input_shape, num_calibration, use_real_data, dataset_path
    )
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    converter.inference_input_type = tf.float32
    converter.inference_output_type = tf.float32

    tflite_model = converter.convert()

    with open(output_path, 'wb') as f:
        f.write(tflite_model)

    size_mb = len(tflite_model) / (1024 * 1024)
    print(f"  INT8 model: {size_mb:.2f} MB -> {output_path}")
    return size_mb

def main():
    parser = argparse.ArgumentParser(description='Export Keras models to TFLite')
    parser.add_argument('--model', required=True, help='Path to Keras model or model name')
    parser.add_argument('--quantize', choices=['float32', 'dynamic', 'int8', 'all'], default='all')
    parser.add_argument('--output', default='models/exported')
    parser.add_argument('--calibration-samples', type=int, default=100)
    parser.add_argument('--use-real-calibration', action='store_true',
                       help='Use real dataset samples for INT8 calibration')
    parser.add_argument('--dataset-path', help='Path to dataset for calibration')

    args = parser.parse_args()

    # Load model
    if os.path.exists(args.model):
        model_path = args.model
    else:
        model_path = f"models/checkpoints/{args.model}.h5"

    if not os.path.exists(model_path):
        print(f"Error: Model not found at {model_path}")
        return 1

    print(f"Loading model from {model_path}...")
    model = tf.keras.models.load_model(model_path)

    # Get input shape
    input_shape = model.input_shape[1:]
    print(f"Model input shape: {input_shape}")

    # Create output directory
    os.makedirs(args.output, exist_ok=True)

    # Generate output file names
    model_name = Path(model_path).stem
    base_output = os.path.join(args.output, model_name)

    # Export models
    sizes = {}

    if args.quantize in ['float32', 'all']:
        output_path = f"{base_output}_float32.tflite"
        sizes['float32'] = export_float32(model, output_path)

    if args.quantize in ['dynamic', 'all']:
        output_path = f"{base_output}_dynamic.tflite"
        sizes['dynamic'] = export_dynamic_range(model, output_path)

    if args.quantize in ['int8', 'all']:
        output_path = f"{base_output}_int8.tflite"
        sizes['int8'] = export_int8(model, input_shape, output_path,
                                    args.calibration_samples,
                                    args.use_real_calibration,
                                    args.dataset_path)

    # Save export report
    report = {
        'model': model_path,
        'input_shape': list(input_shape),
        'export_sizes_mb': sizes,
        'calibration_samples': args.calibration_samples if 'int8' in sizes else None
    }

    report_path = os.path.join(args.output, f"{model_name}_export_report.json")
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\nExport report saved to {report_path}")
    print("\nExport complete!")

    return 0

if __name__ == '__main__':
    exit(main())
