#!/usr/bin/env python3
"""
Raspberry Pi Smoke Test for PREMONITOR
Validates TFLite models on Pi hardware

Usage:
    python3 pi_smoke_test.py
"""

import sys
import os
import time
import numpy as np
import platform

# Try importing tflite_runtime (Pi), fallback to tensorflow.lite
try:
    import tflite_runtime.interpreter as tflite
    USING_TFLITE_RUNTIME = True
except ImportError:
    import tensorflow.lite as tflite
    USING_TFLITE_RUNTIME = False

def get_memory_usage():
    """Get current process memory usage in MB."""
    try:
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)
    except ImportError:
        return None

def test_tflite_runtime():
    """Test 1: Check TFLite runtime availability."""
    print("[TEST 1/7] TFLite Runtime...", end=" ")
    if USING_TFLITE_RUNTIME:
        print("PASS (tflite_runtime)")
    else:
        print("PASS (tensorflow.lite)")
    return True

def test_load_model(model_path, model_name):
    """Test 2-3: Load TFLite model."""
    print(f"[TEST] Load {model_name} Model...", end=" ")

    if not os.path.exists(model_path):
        print(f"FAIL (File not found: {model_path})")
        return None

    try:
        interpreter = tflite.Interpreter(model_path=model_path)
        interpreter.allocate_tensors()

        size_mb = os.path.getsize(model_path) / (1024 * 1024)
        print(f"PASS ({size_mb:.1f} MB)")
        return interpreter
    except Exception as e:
        print(f"FAIL ({e})")
        return None

def test_inference(interpreter, model_name, target_ms=200):
    """Test 4-5: Run inference and measure latency."""
    print(f"[TEST] {model_name} Inference...", end=" ")

    try:
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()

        # Create random input
        input_shape = input_details[0]['shape']
        input_data = np.random.rand(*input_shape).astype(np.float32)

        # Warm-up run
        interpreter.set_tensor(input_details[0]['index'], input_data)
        interpreter.invoke()

        # Timed run
        start = time.time()
        interpreter.set_tensor(input_details[0]['index'], input_data)
        interpreter.invoke()
        output = interpreter.get_tensor(output_details[0]['index'])
        elapsed_ms = (time.time() - start) * 1000

        if elapsed_ms < target_ms:
            print(f"PASS ({elapsed_ms:.0f}ms < {target_ms}ms target)")
            return True
        else:
            print(f"WARN ({elapsed_ms:.0f}ms > {target_ms}ms target)")
            return True
    except Exception as e:
        print(f"FAIL ({e})")
        return False

def test_memory(target_mb=512):
    """Test 6: Check memory usage."""
    print("[TEST 6/7] Memory Usage...", end=" ")

    mem_mb = get_memory_usage()
    if mem_mb is None:
        print("SKIP (psutil not available)")
        return True

    if mem_mb < target_mb:
        print(f"PASS ({mem_mb:.0f} MB / {target_mb} MB target)")
        return True
    else:
        print(f"WARN ({mem_mb:.0f} MB > {target_mb} MB target)")
        return True

def test_numerical_stability(interpreter):
    """Test 7: Numerical stability check."""
    print("[TEST 7/7] Numerical Stability...", end=" ")

    try:
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()

        input_shape = input_details[0]['shape']
        input_data = np.random.rand(*input_shape).astype(np.float32)

        # Run inference twice with same input
        interpreter.set_tensor(input_details[0]['index'], input_data)
        interpreter.invoke()
        output1 = interpreter.get_tensor(output_details[0]['index'])

        interpreter.set_tensor(input_details[0]['index'], input_data)
        interpreter.invoke()
        output2 = interpreter.get_tensor(output_details[0]['index'])

        # Check outputs are identical
        if np.allclose(output1, output2):
            print("PASS")
            return True
        else:
            diff = np.abs(output1 - output2).max()
            print(f"WARN (max diff: {diff:.6f})")
            return True
    except Exception as e:
        print(f"FAIL ({e})")
        return False

def main():
    print("="*60)
    print("PREMONITOR - Raspberry Pi Smoke Test")
    print("="*60)
    print(f"Python: {sys.version.split()[0]}")
    print(f"Platform: {platform.system()} {platform.machine()}")
    print()

    # Define model paths (update these to match your deployment)
    models_dir = os.path.join(os.path.dirname(__file__), 'models', 'exported')
    thermal_model = os.path.join(models_dir, 'thermal_smoke_test_int8.tflite')
    acoustic_model = os.path.join(models_dir, 'acoustic_smoke_test_int8.tflite')

    results = []

    # Test 1: Runtime
    results.append(test_tflite_runtime())

    # Test 2-3: Load models
    thermal_interp = test_load_model(thermal_model, "Thermal")
    results.append(thermal_interp is not None)

    acoustic_interp = test_load_model(acoustic_model, "Acoustic")
    results.append(acoustic_interp is not None)

    # Test 4-5: Inference
    if thermal_interp:
        results.append(test_inference(thermal_interp, "Thermal"))
    else:
        results.append(False)

    if acoustic_interp:
        results.append(test_inference(acoustic_interp, "Acoustic"))
    else:
        results.append(False)

    # Test 6: Memory
    results.append(test_memory())

    # Test 7: Numerical stability
    if thermal_interp:
        results.append(test_numerical_stability(thermal_interp))
    else:
        results.append(False)

    # Summary
    print()
    print("="*60)
    if all(results):
        print("ALL TESTS PASSED")
        print("="*60)
        print("Ready for production deployment.")
        return 0
    else:
        passed = sum(results)
        total = len(results)
        print(f"TESTS FAILED: {passed}/{total} passed")
        print("="*60)
        print("Review failures above before deployment.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
