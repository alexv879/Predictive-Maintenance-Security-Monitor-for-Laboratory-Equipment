#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Smoke tests for Premonitor project - verify basic imports and module loading.
"""

import sys
import os
from pathlib import Path

# Add pythonsoftware directory to path
project_root = Path(__file__).resolve().parent.parent
pythonsoftware_dir = project_root / 'pythonsoftware'
sys.path.insert(0, str(pythonsoftware_dir))


def test_import_config():
    """Test that config module can be imported."""
    try:
        import config
        assert hasattr(config, 'DEBUG_MODE')
        assert hasattr(config, 'THERMAL_MODEL_PATH')
        assert hasattr(config, 'ACOUSTIC_MODEL_PATH')
        print("[PASS] Config module imports successfully")
        return True
    except Exception as e:
        print(f"[FAIL] Failed to import config: {e}")
        return False


def test_import_utils():
    """Test that utils module can be imported."""
    try:
        import utils
        assert hasattr(utils, 'audio_to_spectrogram')
        assert hasattr(utils, 'load_all_thermal_image_paths')
        print("[PASS] Utils module imports successfully")
        return True
    except Exception as e:
        print(f"[FAIL] Failed to import utils: {e}")
        return False


def test_import_alert_manager():
    """Test that alert_manager module can be imported."""
    try:
        import alert_manager
        assert hasattr(alert_manager, 'send_alert_in_background')
        assert hasattr(alert_manager, 'send_email_alert')
        print("[PASS] Alert manager module imports successfully")
        return True
    except Exception as e:
        print(f"[FAIL] Failed to import alert_manager: {e}")
        return False


def test_import_mock_hardware():
    """Test that mock_hardware module can be imported."""
    try:
        import mock_hardware
        assert hasattr(mock_hardware, 'initialize_mock_data')
        assert hasattr(mock_hardware, 'read_thermal_image')
        print("[PASS] Mock hardware module imports successfully")
        return True
    except Exception as e:
        print(f"[FAIL] Failed to import mock_hardware: {e}")
        return False


def test_import_model_blueprints():
    """Test that model_blueprints module can be imported."""
    try:
        import model_blueprints
        assert hasattr(model_blueprints, 'get_thermal_anomaly_model')
        assert hasattr(model_blueprints, 'get_acoustic_anomaly_model')
        print("[PASS] Model blueprints module imports successfully")
        return True
    except Exception as e:
        print(f"[FAIL] Failed to import model_blueprints: {e}")
        return False


def test_tensorflow_available():
    """Test that TensorFlow is available."""
    try:
        import tensorflow as tf
        print(f"[PASS] TensorFlow {tf.__version__} is available")
        return True
    except Exception as e:
        print(f"[FAIL] TensorFlow not available: {e}")
        return False


def test_librosa_available():
    """Test that librosa is available."""
    try:
        import librosa
        print(f"[PASS] Librosa {librosa.__version__} is available")
        return True
    except Exception as e:
        print(f"[FAIL] Librosa not available: {e}")
        return False


def run_all_tests():
    """Run all smoke tests."""
    print("=" * 60)
    print("PREMONITOR SMOKE TESTS - Module Imports")
    print("=" * 60)

    tests = [
        test_tensorflow_available,
        test_librosa_available,
        test_import_config,
        test_import_utils,
        test_import_alert_manager,
        test_import_mock_hardware,
        test_import_model_blueprints,
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
