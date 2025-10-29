# -*- coding: utf-8 -*-
"""
PREMONITOR Equipment Registry
Central configuration for all monitored equipment across multiple Raspberry Pis.

Each equipment entry defines:
- Unique ID and type
- Physical location
- Assigned Raspberry Pi
- Sensor configuration
- Alert channels
- Equipment-specific thresholds
"""

import os
from typing import Dict, List, Any, Optional, Tuple

# ============================================================================
# EQUIPMENT TYPE DEFINITIONS
# ============================================================================

EQUIPMENT_TYPES = {
    "fridge": {
        "name": "Refrigerator",
        "sensors_required": ["thermal", "acoustic"],
        "sensors_optional": ["gas", "temperature"],
        "models": ["thermal_cnn", "acoustic_cnn", "lstm_ae"],
        "description": "Standard lab refrigerator for sample storage"
    },
    "freezer_ultra_low": {
        "name": "Ultra-Low Freezer (-80°C)",
        "sensors_required": ["thermal", "acoustic", "temperature"],
        "sensors_optional": ["gas"],
        "models": ["thermal_cnn", "acoustic_cnn", "lstm_ae"],
        "description": "Ultra-low temperature freezer for long-term sample storage"
    },
    "incubator": {
        "name": "Incubator",
        "sensors_required": ["thermal", "temperature"],
        "sensors_optional": ["co2", "humidity"],
        "models": ["thermal_cnn", "lstm_ae"],
        "description": "Temperature-controlled incubator for cell cultures"
    },
    "centrifuge": {
        "name": "Centrifuge",
        "sensors_required": ["acoustic"],
        "sensors_optional": ["vibration", "current"],
        "models": ["acoustic_cnn", "lstm_ae"],
        "description": "High-speed centrifuge for sample separation"
    },
    "autoclave": {
        "name": "Autoclave",
        "sensors_required": ["thermal", "acoustic"],
        "sensors_optional": ["pressure"],
        "models": ["thermal_cnn", "acoustic_cnn", "lstm_ae"],
        "description": "Steam sterilization equipment"
    },
    "oven": {
        "name": "Laboratory Oven",
        "sensors_required": ["thermal"],
        "sensors_optional": ["temperature"],
        "models": ["thermal_cnn", "lstm_ae"],
        "description": "Drying and heating oven"
    },
    "water_bath": {
        "name": "Water Bath",
        "sensors_required": ["thermal", "temperature"],
        "sensors_optional": [],
        "models": ["thermal_cnn", "lstm_ae"],
        "description": "Temperature-controlled water bath"
    },
    "vacuum_pump": {
        "name": "Vacuum Pump",
        "sensors_required": ["acoustic"],
        "sensors_optional": ["vibration", "pressure"],
        "models": ["acoustic_cnn", "lstm_ae"],
        "description": "Vacuum pump for filtration and evaporation"
    },
    "fume_hood": {
        "name": "Fume Hood",
        "sensors_required": ["acoustic"],
        "sensors_optional": ["airflow", "gas"],
        "models": ["acoustic_cnn"],
        "description": "Ventilated enclosure for hazardous materials"
    },
    "shaker": {
        "name": "Orbital Shaker",
        "sensors_required": ["acoustic"],
        "sensors_optional": ["vibration"],
        "models": ["acoustic_cnn"],
        "description": "Shaking incubator or orbital shaker"
    }
}

# ============================================================================
# EQUIPMENT-SPECIFIC THRESHOLDS
# ============================================================================

EQUIPMENT_THRESHOLDS = {
    "fridge": {
        "thermal_anomaly_confidence": 0.85,
        "acoustic_anomaly_confidence": 0.85,
        "lstm_reconstruction_threshold": 0.045,
        "fusion_correlation_confidence": 0.60,
        "gas_analog_threshold": 300,
        "temperature_range": (2.0, 8.0)  # °C
    },
    "freezer_ultra_low": {
        "thermal_anomaly_confidence": 0.85,
        "acoustic_anomaly_confidence": 0.80,  # More sensitive (expensive samples)
        "lstm_reconstruction_threshold": 0.040,
        "fusion_correlation_confidence": 0.55,
        "gas_analog_threshold": 300,
        "temperature_range": (-82.0, -78.0)  # °C
    },
    "incubator": {
        "thermal_anomaly_confidence": 0.90,  # Less sensitive (always warm)
        "acoustic_anomaly_confidence": 0.85,
        "lstm_reconstruction_threshold": 0.040,
        "fusion_correlation_confidence": 0.60,
        "temperature_range": (36.5, 37.5),  # °C (cell culture)
        "co2_range": (4.5, 5.5),  # Percent
        "humidity_range": (85, 95)  # Percent
    },
    "centrifuge": {
        "thermal_anomaly_confidence": 0.85,
        "acoustic_anomaly_confidence": 0.75,  # Very sensitive (high RPM, safety critical)
        "lstm_reconstruction_threshold": 0.050,
        "vibration_threshold": 0.5,  # G-force
        "current_threshold": 5.0  # Amps (motor overload)
    },
    "autoclave": {
        "thermal_anomaly_confidence": 0.95,  # Less sensitive (very high temp is normal)
        "acoustic_anomaly_confidence": 0.80,
        "lstm_reconstruction_threshold": 0.055,
        "fusion_correlation_confidence": 0.65,
        "pressure_range": (15, 20)  # PSI
    },
    "oven": {
        "thermal_anomaly_confidence": 0.92,  # High temp is normal
        "acoustic_anomaly_confidence": 0.85,
        "lstm_reconstruction_threshold": 0.045,
        "temperature_max": 250.0  # °C (safety limit)
    },
    "water_bath": {
        "thermal_anomaly_confidence": 0.88,
        "acoustic_anomaly_confidence": 0.85,
        "lstm_reconstruction_threshold": 0.040,
        "temperature_range": (35.0, 40.0)  # °C (typical range)
    },
    "vacuum_pump": {
        "thermal_anomaly_confidence": 0.85,
        "acoustic_anomaly_confidence": 0.78,  # Sensitive to bearing wear
        "lstm_reconstruction_threshold": 0.048,
        "pressure_min": 0.1  # Torr (vacuum quality)
    },
    "fume_hood": {
        "acoustic_anomaly_confidence": 0.82,
        "lstm_reconstruction_threshold": 0.045,
        "airflow_min": 100,  # CFM
        "gas_analog_threshold": 200
    },
    "shaker": {
        "acoustic_anomaly_confidence": 0.80,
        "lstm_reconstruction_threshold": 0.050,
        "vibration_threshold": 0.3  # G-force
    }
}

# ============================================================================
# EQUIPMENT REGISTRY (EDIT THIS TO ADD/REMOVE EQUIPMENT)
# ============================================================================

# ============================================================================
# SINGLE RASPBERRY PI CONFIGURATION
# All equipment monitored from ONE Pi (default: "premonitor_pi")
# 
# IMPORTANT: For single-Pi deployment, all equipment should have the same pi_id.
# The system can handle 3-5 equipment units per Pi depending on sensor density.
# ============================================================================

EQUIPMENT_REGISTRY = [
    # ========================================================================
    # PRIMARY EQUIPMENT (Single Pi Setup)
    # ========================================================================
    {
        "id": "fridge_lab_a_01",
        "type": "fridge",
        "name": "Main Lab Fridge A1",
        "location": "Lab A, Corner near sink",
        "pi_id": "premonitor_pi",  # Single Pi for all equipment
        "sensors": {
            "thermal_camera": {
                "enabled": True,
                "i2c_address": "0x33",
                "fps": 2,
                "resolution": (32, 24)
            },
            "microphone": {
                "enabled": True,
                "device": "hw:1,0",
                "sample_rate": 16000,
                "channels": 1
            },
            "gas_sensor": {
                "enabled": True,
                "gpio_pin": 17,
                "analog_channel": 0,
                "sensor_type": "MQ-2"
            },
            "temperature": {
                "enabled": True,
                "gpio_pin": 4,
                "sensor_type": "DS18B20",
                "device_id": "28-000000000000"
            }
        },
        "alert_channels": ["discord", "email"],
        "maintenance_schedule": "Quarterly",
        "critical": True,
        "notes": "Primary sample storage for Lab A"
    },
    
    # ========================================================================
    # ADDITIONAL EQUIPMENT (Add more as needed - same Pi)
    # To add new equipment, copy a block and change: id, name, location, sensors
    # Keep pi_id as "premonitor_pi" for single-Pi deployment
    # ========================================================================
    
    # Example: Ultra-Low Freezer (DISABLED by default - enable if you have one)
    # {
    #     "id": "freezer_ultra_low_01",
    #     "type": "freezer_ultra_low",
    #     "name": "Ultra-Low Freezer -80°C",
    #     "location": "Lab A, Cold room",
    #     "pi_id": "premonitor_pi",  # Same Pi
    #     "sensors": {
    #         "thermal_camera": {
    #             "enabled": True,
    #             "i2c_address": "0x34",  # Different I2C address
    #             "fps": 2,
    #             "resolution": (32, 24)
    #         },
    #         "microphone": {
    #             "enabled": True,
    #             "device": "hw:2,0",  # Different audio device
    #             "sample_rate": 16000,
    #             "channels": 1
    #         },
    #         "temperature": {
    #             "enabled": True,
    #             "gpio_pin": 5,  # Different GPIO pin
    #             "sensor_type": "DS18B20",
    #             "device_id": "28-000000000001"
    #         }
    #     },
    #     "alert_channels": ["discord", "email", "sms"],
    #     "maintenance_schedule": "Monthly",
    #     "critical": True,
    #     "notes": "CRITICAL - Contains irreplaceable samples worth $100K+"
    # },
    
    # Example: Incubator (DISABLED by default - enable if you have one)
    # {
    #     "id": "incubator_cell_01",
    #     "type": "incubator",
    #     "name": "Cell Culture Incubator #1",
    #     "location": "Lab B, Cell culture room",
    #     "pi_id": "premonitor_pi",  # Same Pi
    #     "sensors": {
    #         "thermal_camera": {
    #             "enabled": True,
    #             "i2c_address": "0x35",  # Different I2C address
    #             "fps": 2,
    #             "resolution": (32, 24)
    #         },
    #         "temperature": {
    #             "enabled": True,
    #             "gpio_pin": 6,
    #             "sensor_type": "DS18B20",
    #             "device_id": "28-000000000002"
    #         }
    #     },
    #     "alert_channels": ["discord", "email"],
    #     "maintenance_schedule": "Monthly",
    #     "critical": True,
    #     "notes": "Contains live cell cultures - temperature critical"
    # },
    
    # Example: Centrifuge (DISABLED by default - enable if you have one)
    # {
    #     "id": "centrifuge_01",
    #     "type": "centrifuge",
    #     "name": "Benchtop Centrifuge #1",
    #     "location": "Lab B, Bench 3",
    #     "pi_id": "premonitor_pi",  # Same Pi
    #     "sensors": {
    #         "microphone": {
    #             "enabled": True,
    #             "device": "hw:3,0",  # Different audio device
    #             "sample_rate": 16000,
    #             "channels": 1
    #         },
    #         "vibration": {
    #             "enabled": True,
    #             "i2c_address": "0x53",
    #             "sensor_type": "ADXL345",
    #             "range": "±16g"
    #         }
    #     },
    #     "alert_channels": ["discord", "email"],
    #     "maintenance_schedule": "Semi-annually",
    #     "critical": False,
    #     "notes": "High-speed centrifuge - safety critical during operation"
    # },
]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_equipment_by_pi(pi_id: str) -> List[Dict[str, Any]]:
    """
    Get all equipment assigned to a specific Raspberry Pi.

    Args:
        pi_id: Unique identifier for the Raspberry Pi (e.g., "premonitor_pi")

    Returns:
        List of equipment configuration dictionaries

    Example:
        >>> equipment = get_equipment_by_pi("premonitor_pi")
        >>> print(len(equipment))
        1
    """
    return [eq for eq in EQUIPMENT_REGISTRY if eq["pi_id"] == pi_id]


def get_equipment_by_id(equipment_id: str) -> Optional[Dict[str, Any]]:
    """
    Get specific equipment configuration by its unique ID.

    Args:
        equipment_id: Unique equipment identifier (e.g., "fridge_lab_a_01")

    Returns:
        Equipment configuration dict, or None if not found

    Example:
        >>> eq = get_equipment_by_id("fridge_lab_a_01")
        >>> print(eq['name'])
        'Main Lab Fridge A1'
    """
    for eq in EQUIPMENT_REGISTRY:
        if eq["id"] == equipment_id:
            return eq
    return None


def get_equipment_thresholds(equipment_type: str) -> Dict[str, Any]:
    """
    Get thresholds for a specific equipment type.

    Args:
        equipment_type: Type of equipment (e.g., "fridge", "freezer_ultra_low")

    Returns:
        Dictionary of threshold values for the equipment type
    """
    return EQUIPMENT_THRESHOLDS.get(equipment_type, EQUIPMENT_THRESHOLDS["fridge"])


def get_critical_equipment() -> List[Dict[str, Any]]:
    """
    Get all equipment marked as critical.

    Returns:
        List of critical equipment configurations
    """
    return [eq for eq in EQUIPMENT_REGISTRY if eq.get("critical", False)]


def validate_equipment_config(equipment: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate equipment configuration against type requirements.

    Checks that all required sensors for the equipment type are present
    and enabled in the configuration.

    Args:
        equipment: Equipment configuration dictionary

    Returns:
        Tuple of (is_valid: bool, message: str)
        - If valid: (True, "Configuration valid")
        - If invalid: (False, "Error description")

    Example:
        >>> eq = {"type": "fridge", "sensors": {"thermal_camera": {"enabled": True}}}
        >>> valid, msg = validate_equipment_config(eq)
        >>> print(f"{valid}: {msg}")
        False: Required sensor missing: acoustic (config key: microphone)
    """
    eq_type = equipment["type"]
    if eq_type not in EQUIPMENT_TYPES:
        return False, f"Unknown equipment type: {eq_type}"
    
    type_def = EQUIPMENT_TYPES[eq_type]
    sensors_config = equipment.get("sensors", {})
    
    # Map sensor type names to config keys
    sensor_name_mapping = {
        "thermal": "thermal_camera",
        "acoustic": "microphone",
        "temperature": "temperature",
        "gas": "gas_sensor",
        "vibration": "vibration",
        "current": "current",
        "co2": "co2",
        "humidity": "humidity",
        "pressure": "pressure",
        "airflow": "airflow"
    }
    
    # Check required sensors
    for required_sensor in type_def["sensors_required"]:
        # Map sensor type to config key
        config_key = sensor_name_mapping.get(required_sensor, required_sensor)
        if config_key not in sensors_config or not sensors_config[config_key].get("enabled", False):
            return False, f"Required sensor missing: {required_sensor} (config key: {config_key})"
    
    return True, "Configuration valid"

def get_pi_id() -> str:
    """
    Get the current Raspberry Pi ID from hostname or environment variable.

    Returns:
        Pi identifier string (default: "premonitor_pi")
    """
    # Try environment variable first
    pi_id = os.environ.get("PREMONITOR_PI_ID")
    if pi_id:
        return pi_id
    
    # Try hostname
    try:
        with open("/etc/hostname", "r") as f:
            hostname = f.read().strip()
            return hostname
    except:
        pass
    
    # Default fallback for single-Pi deployment
    return "premonitor_pi"

# ============================================================================
# VALIDATION ON IMPORT
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print(" " * 25 + "EQUIPMENT REGISTRY VALIDATION")
    print("=" * 80)
    print()
    
    # Validate all equipment
    print(f"Total equipment registered: {len(EQUIPMENT_REGISTRY)}")
    print(f"Equipment types available: {len(EQUIPMENT_TYPES)}")
    print(f"Raspberry Pis in use: {len(set(eq['pi_id'] for eq in EQUIPMENT_REGISTRY))}")
    print()
    
    # Validate each equipment
    errors = []
    for eq in EQUIPMENT_REGISTRY:
        valid, msg = validate_equipment_config(eq)
        if not valid:
            errors.append(f"  ✗ {eq['id']}: {msg}")
    
    if errors:
        print("❌ Configuration Errors:")
        for error in errors:
            print(error)
    else:
        print("✅ All equipment configurations valid!")
    
    print()
    print("Equipment by Pi:")
    for pi_id in sorted(set(eq['pi_id'] for eq in EQUIPMENT_REGISTRY)):
        equipment = get_equipment_by_pi(pi_id)
        print(f"\n{pi_id}:")
        for eq in equipment:
            critical = "🔴 CRITICAL" if eq.get("critical", False) else ""
            print(f"  - {eq['id']}: {eq['name']} {critical}")
    
    print()
    print("=" * 80)
