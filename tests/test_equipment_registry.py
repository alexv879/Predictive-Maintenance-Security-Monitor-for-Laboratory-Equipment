#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for equipment_registry.py
"""

import sys
from pathlib import Path

# Add pythonsoftware to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'pythonsoftware'))

import equipment_registry as er


def test_equipment_types_defined():
    """Test that all equipment types are defined."""
    assert len(er.EQUIPMENT_TYPES) > 0
    assert 'fridge' in er.EQUIPMENT_TYPES
    assert 'freezer_ultra_low' in er.EQUIPMENT_TYPES
    print("[PASS] Equipment types defined")


def test_get_equipment_by_pi():
    """Test getting equipment by Pi ID."""
    equipment = er.get_equipment_by_pi("premonitor_pi")
    assert isinstance(equipment, list)
    assert len(equipment) >= 1  # At least one equipment registered
    print(f"[PASS] Found {len(equipment)} equipment for premonitor_pi")


def test_get_equipment_by_id():
    """Test getting equipment by ID."""
    eq = er.get_equipment_by_id("fridge_lab_a_01")
    assert eq is not None
    assert eq['type'] == 'fridge'
    assert eq['name'] == 'Main Lab Fridge A1'
    print("[PASS] Equipment retrieval by ID works")


def test_get_nonexistent_equipment():
    """Test that nonexistent equipment returns None."""
    eq = er.get_equipment_by_id("nonexistent_id_12345")
    assert eq is None
    print("[PASS] Nonexistent equipment returns None")


def test_validate_valid_config():
    """Test validation of valid equipment config."""
    eq = er.get_equipment_by_id("fridge_lab_a_01")
    valid, msg = er.validate_equipment_config(eq)
    assert valid, f"Validation failed: {msg}"
    print("[PASS] Valid config passes validation")


def test_validate_invalid_config():
    """Test validation catches invalid config."""
    invalid_eq = {
        "id": "test_invalid",
        "type": "fridge",
        "sensors": {
            # Missing required thermal_camera and microphone
            "gas_sensor": {"enabled": True}
        }
    }
    valid, msg = er.validate_equipment_config(invalid_eq)
    assert not valid
    assert "thermal" in msg.lower() or "acoustic" in msg.lower()
    print(f"[PASS] Invalid config detected: {msg}")


def test_get_critical_equipment():
    """Test getting critical equipment."""
    critical = er.get_critical_equipment()
    assert isinstance(critical, list)
    # fridge_lab_a_01 is marked critical=True
    assert any(eq['id'] == 'fridge_lab_a_01' for eq in critical)
    print(f"[PASS] Found {len(critical)} critical equipment units")


def test_thresholds_defined():
    """Test that thresholds are defined for all equipment types."""
    for eq_type in er.EQUIPMENT_TYPES.keys():
        thresholds = er.get_equipment_thresholds(eq_type)
        assert isinstance(thresholds, dict)
        assert len(thresholds) > 0
    print("[PASS] Thresholds defined for all equipment types")


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("EQUIPMENT REGISTRY UNIT TESTS")
    print("=" * 60)

    tests = [
        test_equipment_types_defined,
        test_get_equipment_by_pi,
        test_get_equipment_by_id,
        test_get_nonexistent_equipment,
        test_validate_valid_config,
        test_validate_invalid_config,
        test_get_critical_equipment,
        test_thresholds_defined,
    ]

    results = []
    for test in tests:
        try:
            test()
            results.append(True)
        except AssertionError as e:
            print(f"[FAIL] {test.__name__}: {e}")
            results.append(False)
        except Exception as e:
            print(f"[ERROR] {test.__name__} crashed: {e}")
            results.append(False)

    print("=" * 60)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)

    return all(results)


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
