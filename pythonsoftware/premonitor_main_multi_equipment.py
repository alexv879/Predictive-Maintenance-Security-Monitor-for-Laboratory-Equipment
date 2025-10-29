# -*- coding: utf-8 -*-
"""
PREMONITOR Multi-Equipment Monitoring System
Main script for monitoring multiple lab equipment units from a single Raspberry Pi.

This version:
- Loads equipment configuration from equipment_registry.py
- Monitors all equipment assigned to this Pi
- Uses equipment-specific thresholds
- Routes alerts per equipment configuration
- Handles multiple sensor types
"""

import time
import numpy as np
from datetime import datetime
import os
import json
import sys
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('premonitor_multi')

# Try importing tflite_runtime first (preferred on Pi), fallback to tensorflow
try:
    import tflite_runtime.interpreter as tflite
    logger.info("Using tflite_runtime for inference")
    USING_TFLITE_RUNTIME = True
except ImportError:
    try:
        import tensorflow as tf
        tflite = tf.lite
        logger.info("Using tensorflow.lite for inference")
        USING_TFLITE_RUNTIME = False
    except ImportError:
        logger.critical("Neither tflite_runtime nor tensorflow.lite could be imported")
        sys.exit(1)

# Import our custom project files
try:
    import config
    import alert_manager
    import equipment_registry
    import security_monitor
    # For the MVP, we use the mock hardware. To switch to real hardware,
    # you would change this line to: import hardware_drivers as hardware
    import mock_hardware as hardware
    logger.info("Successfully imported project modules")
except ImportError as e:
    logger.critical(f"Failed to import project modules: {e}")
    sys.exit(1)

# --- Global variables for loaded AI models ---
thermal_interpreter = None
acoustic_interpreter = None
lstm_interpreter = None

# --- Equipment state tracking ---
equipment_states = {}  # Dict[equipment_id, Dict[sensor_type, value]]
equipment_lstm_buffers = {}  # Dict[equipment_id, List[sensor_readings]]

# ============================================================================
# GAS SENSOR CALIBRATION HELPER
# ============================================================================

def calibrate_gas_sensor(adc_value: float, sensor_type: str = "MQ-2",
                          calibration_params: dict = None) -> dict:
    """
    Convert gas sensor ADC value to approximate PPM concentration.

    Args:
        adc_value: Raw ADC reading (0-1023 for 10-bit ADC)
        sensor_type: Sensor model ("MQ-2", "MQ-135", etc.)
        calibration_params: Optional dict with 'zero_ppm_adc' and 'sensitivity'

    Returns:
        dict with 'adc_value', 'ppm_estimate', 'sensor_type', 'calibrated'

    Note:
        Default calibration is a rough linear approximation.
        For accurate readings, perform proper sensor calibration:
        1. Place sensor in clean air, record ADC value (zero_ppm_adc)
        2. Expose to known gas concentration, calculate sensitivity
        3. Store calibration_params in equipment registry
    """
    result = {
        "adc_value": adc_value,
        "sensor_type": sensor_type,
        "calibrated": False,
        "ppm_estimate": None
    }

    # Use custom calibration if provided
    if calibration_params and "zero_ppm_adc" in calibration_params and "sensitivity" in calibration_params:
        zero = calibration_params["zero_ppm_adc"]
        sensitivity = calibration_params["sensitivity"]  # PPM per ADC unit
        ppm = max(0, (adc_value - zero) * sensitivity)
        result["ppm_estimate"] = round(ppm, 1)
        result["calibrated"] = True
        return result

    # Rough uncalibrated estimate (MQ-2 typical: 300 ADC ≈ 300 PPM, 1:1 approximation)
    # This is NOT accurate without proper calibration
    result["ppm_estimate"] = round(adc_value, 0)  # Simple 1:1 mapping
    result["calibrated"] = False

    return result

# ============================================================================
# LSTM FEATURE VECTOR BUILDER (Deterministic Ordering)
# ============================================================================

def build_lstm_feature_vector(readings: Dict[str, Any], equipment_type: str) -> np.ndarray:
    """
    Build deterministic feature vector for LSTM input from sensor readings.

    Feature order is fixed regardless of sensor read order:
    [temperature, gas, vibration, current, acoustic_rms, thermal_mean]

    Args:
        readings: Sensor readings dict from read_equipment_sensors()
        equipment_type: Equipment type (from equipment_registry)

    Returns:
        NumPy array of shape (n_features,) with NaN for missing sensors

    Note:
        Training pipeline must use the same feature order!
        Missing sensors are filled with NaN (will be handled in normalization).
    """
    sensors = readings.get("sensors", {})

    # Fixed feature order (must match training pipeline)
    feature_vector = []

    # Feature 0: Temperature (scalar)
    feature_vector.append(float(sensors.get("temperature", np.nan)))

    # Feature 1: Gas (scalar)
    feature_vector.append(float(sensors.get("gas", np.nan)))

    # Feature 2: Vibration (scalar)
    feature_vector.append(float(sensors.get("vibration", np.nan)))

    # Feature 3: Current (scalar)
    feature_vector.append(float(sensors.get("current", np.nan)))

    # Feature 4: Acoustic RMS (computed from audio array)
    audio = sensors.get("audio")
    if audio is not None and isinstance(audio, np.ndarray):
        acoustic_rms = np.sqrt(np.mean(audio ** 2))
        feature_vector.append(float(acoustic_rms))
    else:
        feature_vector.append(np.nan)

    # Feature 5: Thermal mean (computed from thermal array)
    thermal = sensors.get("thermal")
    if thermal is not None and isinstance(thermal, np.ndarray):
        thermal_mean = np.mean(thermal)
        feature_vector.append(float(thermal_mean))
    else:
        feature_vector.append(np.nan)

    return np.array(feature_vector, dtype=np.float32)

# ============================================================================
# MODEL LOADING
# ============================================================================

def load_tflite_model(model_path: str, model_name: str):
    """
    Load a TensorFlow Lite model and return the interpreter.
    """
    try:
        if not os.path.exists(model_path):
            logger.error(f"{model_name} model not found: {model_path}")
            return None
        
        logger.info(f"Loading {model_name} model from: {model_path}")
        interpreter = tflite.Interpreter(model_path=model_path)
        interpreter.allocate_tensors()
        
        # Log input/output details
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()
        logger.info(f"{model_name} input shape: {input_details[0]['shape']}")
        logger.info(f"{model_name} output shape: {output_details[0]['shape']}")
        
        return interpreter
    except Exception as e:
        logger.error(f"Failed to load {model_name} model: {e}")
        return None

def startup_check():
    """
    Verify all required model paths, config entries, and dependencies before starting.
    Returns True if all checks pass, False otherwise.
    """
    logger.info("Running startup checks...")

    all_checks_passed = True

    # Check config module attributes
    required_config_attrs = [
        'THERMAL_MODEL_PATH',
        'ACOUSTIC_MODEL_PATH',
        'SENSOR_READ_INTERVAL'
    ]

    for attr in required_config_attrs:
        if not hasattr(config, attr):
            logger.error(f"Missing required config attribute: {attr}")
            all_checks_passed = False
        else:
            logger.debug(f"Config check passed: {attr} = {getattr(config, attr)}")

    # Check equipment registry
    pi_id = equipment_registry.get_pi_id()
    equipment_list = equipment_registry.get_equipment_by_pi(pi_id)
    
    if not equipment_list:
        logger.error(f"No equipment assigned to Pi: {pi_id}")
        all_checks_passed = False
    else:
        logger.info(f"Found {len(equipment_list)} equipment units assigned to this Pi")
        for eq in equipment_list:
            valid, msg = equipment_registry.validate_equipment_config(eq)
            if not valid:
                logger.error(f"Invalid config for {eq['id']}: {msg}")
                all_checks_passed = False

    # Check model files exist
    model_paths = {
        'thermal': getattr(config, 'THERMAL_MODEL_PATH', ''),
        'acoustic': getattr(config, 'ACOUSTIC_MODEL_PATH', ''),
        'lstm': getattr(config, 'LSTM_MODEL_PATH', '')
    }

    for model_name, model_path in model_paths.items():
        if not model_path:
            logger.warning(f"{model_name.upper()}_MODEL_PATH is not configured")
        elif not os.path.exists(model_path):
            logger.warning(f"{model_name.capitalize()} model not found: {model_path}")

    return all_checks_passed

def load_models():
    """
    Load all TFLite models into memory.
    """
    global thermal_interpreter, acoustic_interpreter, lstm_interpreter
    
    logger.info("Loading AI models...")
    
    # Load thermal model
    if hasattr(config, 'THERMAL_MODEL_PATH') and config.THERMAL_MODEL_PATH:
        thermal_interpreter = load_tflite_model(config.THERMAL_MODEL_PATH, "Thermal")
    
    # Load acoustic model
    if hasattr(config, 'ACOUSTIC_MODEL_PATH') and config.ACOUSTIC_MODEL_PATH:
        acoustic_interpreter = load_tflite_model(config.ACOUSTIC_MODEL_PATH, "Acoustic")
    
    # Load LSTM model
    if hasattr(config, 'LSTM_MODEL_PATH') and config.LSTM_MODEL_PATH:
        lstm_interpreter = load_tflite_model(config.LSTM_MODEL_PATH, "LSTM-AE")
    
    # Check if at least one model loaded
    if not any([thermal_interpreter, acoustic_interpreter, lstm_interpreter]):
        logger.error("No models loaded successfully. Exiting.")
        return False
    
    logger.info("Model loading complete")
    return True

# ============================================================================
# SENSOR READING
# ============================================================================

def read_equipment_sensors(equipment: Dict[str, Any]) -> Dict[str, Any]:
    """
    Read all enabled sensors for a specific equipment unit.
    Returns dict of sensor readings.
    """
    readings = {
        "equipment_id": equipment["id"],
        "timestamp": datetime.now().isoformat(),
        "sensors": {}
    }
    
    sensors_config = equipment.get("sensors", {})
    
    # Thermal camera
    if sensors_config.get("thermal_camera", {}).get("enabled", False):
        try:
            thermal_data = hardware.read_thermal_camera()
            readings["sensors"]["thermal"] = thermal_data
        except Exception as e:
            logger.error(f"[{equipment['id']}] Error reading thermal camera: {e}")
    
    # Microphone
    if sensors_config.get("microphone", {}).get("enabled", False):
        try:
            audio_data = hardware.read_microphone()
            readings["sensors"]["audio"] = audio_data
        except Exception as e:
            logger.error(f"[{equipment['id']}] Error reading microphone: {e}")
    
    # Gas sensor
    if sensors_config.get("gas_sensor", {}).get("enabled", False):
        try:
            gas_value = hardware.read_gas_sensor()
            readings["sensors"]["gas"] = gas_value
        except Exception as e:
            logger.error(f"[{equipment['id']}] Error reading gas sensor: {e}")
    
    # Temperature sensor
    if sensors_config.get("temperature", {}).get("enabled", False):
        try:
            temp_value = hardware.read_temperature()
            readings["sensors"]["temperature"] = temp_value
        except Exception as e:
            logger.error(f"[{equipment['id']}] Error reading temperature: {e}")

    # CO2 sensor
    if sensors_config.get("co2", {}).get("enabled", False):
        try:
            co2_value = hardware.read_co2_sensor()
            readings["sensors"]["co2"] = co2_value
        except Exception as e:
            logger.error(f"[{equipment['id']}] Error reading CO2 sensor: {e}")

    # Oxygen sensor
    if sensors_config.get("oxygen", {}).get("enabled", False):
        try:
            oxygen_value = hardware.read_oxygen_sensor()
            readings["sensors"]["oxygen"] = oxygen_value
        except Exception as e:
            logger.error(f"[{equipment['id']}] Error reading oxygen sensor: {e}")

    # Vibration sensor
    if sensors_config.get("vibration", {}).get("enabled", False):
        try:
            vibration_value = hardware.read_vibration_sensor()
            readings["sensors"]["vibration"] = vibration_value
        except Exception as e:
            logger.error(f"[{equipment['id']}] Error reading vibration sensor: {e}")

    # Current sensor
    if sensors_config.get("current", {}).get("enabled", False):
        try:
            current_value = hardware.read_current_sensor()
            readings["sensors"]["current"] = current_value
        except Exception as e:
            logger.error(f"[{equipment['id']}] Error reading current sensor: {e}")

    return readings

# ============================================================================
# AI INFERENCE
# ============================================================================

def run_thermal_inference(thermal_data: np.ndarray, equipment_id: str) -> Dict[str, Any]:
    """
    Run thermal anomaly detection model.
    """
    if thermal_interpreter is None:
        return {"error": "Thermal model not loaded"}
    
    try:
        # Prepare input
        input_details = thermal_interpreter.get_input_details()
        output_details = thermal_interpreter.get_output_details()
        
        # Normalize and reshape
        thermal_normalized = thermal_data.astype(np.float32) / 255.0
        input_shape = input_details[0]['shape']
        thermal_reshaped = np.expand_dims(thermal_normalized, axis=0)
        
        # Run inference
        thermal_interpreter.set_tensor(input_details[0]['index'], thermal_reshaped)
        thermal_interpreter.invoke()
        output = thermal_interpreter.get_tensor(output_details[0]['index'])
        
        # Parse results
        anomaly_confidence = float(output[0][0])
        
        return {
            "model": "thermal_cnn",
            "equipment_id": equipment_id,
            "anomaly_confidence": anomaly_confidence,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"[{equipment_id}] Thermal inference error: {e}")
        return {"error": str(e)}

def run_acoustic_inference(audio_data: np.ndarray, equipment_id: str) -> Dict[str, Any]:
    """
    Run acoustic anomaly detection model.
    """
    if acoustic_interpreter is None:
        return {"error": "Acoustic model not loaded"}
    
    try:
        # Prepare input (assume spectrogram or similar preprocessing)
        input_details = acoustic_interpreter.get_input_details()
        output_details = acoustic_interpreter.get_output_details()
        
        # Normalize
        audio_normalized = audio_data.astype(np.float32)
        audio_reshaped = np.expand_dims(audio_normalized, axis=0)
        
        # Run inference
        acoustic_interpreter.set_tensor(input_details[0]['index'], audio_reshaped)
        acoustic_interpreter.invoke()
        output = acoustic_interpreter.get_tensor(output_details[0]['index'])
        
        # Parse results
        anomaly_confidence = float(output[0][0])
        
        return {
            "model": "acoustic_cnn",
            "equipment_id": equipment_id,
            "anomaly_confidence": anomaly_confidence,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"[{equipment_id}] Acoustic inference error: {e}")
        return {"error": str(e)}

def run_lstm_inference(sensor_buffer: np.ndarray, equipment_id: str) -> Dict[str, Any]:
    """
    Run LSTM autoencoder for time-series anomaly detection.

    Args:
        sensor_buffer: NumPy array of shape (time_steps, n_features)
        equipment_id: Equipment identifier
    """
    if lstm_interpreter is None:
        return {"error": "LSTM model not loaded"}

    try:
        input_details = lstm_interpreter.get_input_details()
        output_details = lstm_interpreter.get_output_details()

        expected_shape = input_details[0]['shape']  # e.g., (1, 50, 6)

        # Validate input shape matches model
        if sensor_buffer.shape[0] != expected_shape[1]:
            return {"error": f"LSTM buffer has {sensor_buffer.shape[0]} time steps, expected {expected_shape[1]}"}
        if sensor_buffer.shape[1] != expected_shape[2]:
            return {"error": f"LSTM buffer has {sensor_buffer.shape[1]} features, expected {expected_shape[2]}"}

        # Normalize (handle NaN values from missing sensors)
        sequence_normalized = np.nan_to_num(sensor_buffer, nan=0.0)  # Replace NaN with 0
        sequence_normalized = (sequence_normalized - np.mean(sequence_normalized)) / (np.std(sequence_normalized) + 1e-7)
        sequence_reshaped = np.expand_dims(sequence_normalized, axis=0).astype(np.float32)

        # Run inference
        lstm_interpreter.set_tensor(input_details[0]['index'], sequence_reshaped)
        lstm_interpreter.invoke()
        reconstructed = lstm_interpreter.get_tensor(output_details[0]['index'])

        # Calculate reconstruction error
        mse = np.mean((sequence_normalized - reconstructed[0]) ** 2)

        return {
            "model": "lstm_ae",
            "equipment_id": equipment_id,
            "reconstruction_error": float(mse),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"[{equipment_id}] LSTM inference error: {e}")
        return {"error": str(e)}

# ============================================================================
# ANOMALY DETECTION & ALERTS
# ============================================================================

def check_anomaly_and_alert(equipment: Dict[str, Any], inference_results: List[Dict[str, Any]]):
    """
    Check inference results against equipment-specific thresholds and trigger alerts.
    """
    equipment_id = equipment["id"]
    equipment_type = equipment["type"]
    thresholds = equipment_registry.get_equipment_thresholds(equipment_type)
    
    anomalies_detected = []
    
    for result in inference_results:
        if "error" in result:
            continue
        
        model_type = result["model"]
        
        # Thermal model
        if model_type == "thermal_cnn":
            confidence = result["anomaly_confidence"]
            threshold = thresholds.get("thermal_anomaly_confidence", 0.85)
            if confidence > threshold:
                anomalies_detected.append({
                    "type": "thermal",
                    "confidence": confidence,
                    "threshold": threshold,
                    "message": f"Thermal anomaly detected (confidence: {confidence:.2f})"
                })
        
        # Acoustic model
        elif model_type == "acoustic_cnn":
            confidence = result["anomaly_confidence"]
            threshold = thresholds.get("acoustic_anomaly_confidence", 0.85)
            if confidence > threshold:
                anomalies_detected.append({
                    "type": "acoustic",
                    "confidence": confidence,
                    "threshold": threshold,
                    "message": f"Acoustic anomaly detected (confidence: {confidence:.2f})"
                })
        
        # LSTM model
        elif model_type == "lstm_ae":
            reconstruction_error = result["reconstruction_error"]
            threshold = thresholds.get("lstm_reconstruction_threshold", 0.045)
            if reconstruction_error > threshold:
                anomalies_detected.append({
                    "type": "lstm_degradation",
                    "reconstruction_error": reconstruction_error,
                    "threshold": threshold,
                    "message": f"Performance degradation detected (error: {reconstruction_error:.4f})"
                })
    
    # Trigger alerts if anomalies detected
    if anomalies_detected:
        alert_channels = equipment.get("alert_channels", ["discord"])
        
        alert_message = f"🚨 ANOMALY DETECTED: {equipment['name']} ({equipment_id})\n"
        alert_message += f"Location: {equipment.get('location', 'Unknown')}\n"
        alert_message += f"Equipment Type: {equipment_type}\n\n"
        
        for anomaly in anomalies_detected:
            alert_message += f"• {anomaly['message']}\n"
        
        alert_message += f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Send alerts to configured channels
        for channel in alert_channels:
            try:
                if channel == "discord":
                    alert_manager.send_discord_alert(alert_message)
                elif channel == "email":
                    alert_manager.send_email_alert(f"Anomaly: {equipment['name']}", alert_message)
                elif channel == "sms":
                    # Implement SMS if needed
                    logger.warning(f"SMS alerts not implemented yet for {equipment_id}")
            except Exception as e:
                logger.error(f"[{equipment_id}] Failed to send alert via {channel}: {e}")
        
        logger.warning(f"[{equipment_id}] Anomaly alert sent: {len(anomalies_detected)} issues detected")


def check_raw_sensor_thresholds(equipment: Dict[str, Any], readings: Dict[str, Any]):
    """
    Check raw (non-AI) sensor values against configured thresholds and send immediate alerts.

    This covers:
      - Temperature hard limits (possible fire / fridge out-of-range)
      - Gas analog thresholds (MQ-series sensors)
      - CO2 ranges (if configured for incubators)
      - Optional oxygen sensor checks (if 'oxygen' sensor present and thresholds configured)

    This is intentionally simple and acts as a fast fail-safe in addition to AI models.
    """
    equipment_id = equipment["id"]
    equipment_type = equipment["type"]
    thresholds = equipment_registry.get_equipment_thresholds(equipment_type)

    sensors = readings.get("sensors", {})

    alerts = []

    # Temperature checks
    if "temperature" in sensors:
        try:
            temp_val = float(sensors["temperature"])
            # Equipment-specific acceptable range
            temp_range = thresholds.get("temperature_range")
            if temp_range and (temp_val < temp_range[0] or temp_val > temp_range[1]):
                alerts.append(f"Temperature out of expected range: {temp_val:.2f}°C (expected {temp_range})")

            # Hard critical temperature (fire risk)
            critical_c = getattr(config, 'THERMAL_CRITICAL_THRESHOLD_C', None)
            if critical_c is not None and temp_val >= critical_c:
                alerts.append(f"CRITICAL: High temperature detected: {temp_val:.2f}°C >= {critical_c}°C")
        except Exception:
            logger.debug(f"[{equipment_id}] Could not parse temperature sensor value: {sensors.get('temperature')}")

    # Gas sensor checks (analog value)
    if "gas" in sensors:
        try:
            gas_val = float(sensors["gas"])
            gas_threshold = thresholds.get("gas_analog_threshold", getattr(config, 'GAS_ANALOG_THRESHOLD', None))
            if gas_threshold is not None and gas_val >= gas_threshold:
                alerts.append(f"Gas sensor above threshold: {gas_val} >= {gas_threshold}")
        except Exception:
            logger.debug(f"[{equipment_id}] Could not parse gas sensor value: {sensors.get('gas')}")

    # CO2 checks (percent)
    if "co2" in sensors:
        try:
            co2_val = float(sensors["co2"])
            co2_range = thresholds.get("co2_range")
            if co2_range and (co2_val < co2_range[0] or co2_val > co2_range[1]):
                alerts.append(f"CO2 level out of expected range: {co2_val:.2f}% (expected {co2_range})")
        except Exception:
            logger.debug(f"[{equipment_id}] Could not parse CO2 sensor value: {sensors.get('co2')}")

    # Oxygen checks (optional) - user can add 'oxygen_min' to equipment thresholds
    if "oxygen" in sensors:
        try:
            oxy_val = float(sensors["oxygen"])
            oxy_min = thresholds.get("oxygen_min")
            if oxy_min is not None and oxy_val < oxy_min:
                alerts.append(f"Low oxygen detected: {oxy_val:.2f}% < {oxy_min}%")
        except Exception:
            logger.debug(f"[{equipment_id}] Could not parse oxygen sensor value: {sensors.get('oxygen')}")

    # Vibration checks (mechanical fault detection)
    if "vibration" in sensors:
        try:
            vib_val = float(sensors["vibration"])
            vib_threshold = thresholds.get("vibration_threshold")
            if vib_threshold is not None and vib_val >= vib_threshold:
                alerts.append(f"High vibration detected: {vib_val:.2f}G >= {vib_threshold}G (possible bearing wear)")
        except Exception:
            logger.debug(f"[{equipment_id}] Could not parse vibration sensor value: {sensors.get('vibration')}")

    # Current checks (motor overload detection)
    if "current" in sensors:
        try:
            current_val = float(sensors["current"])
            current_threshold = thresholds.get("current_threshold")
            if current_threshold is not None and current_val >= current_threshold:
                alerts.append(f"Motor overload detected: {current_val:.2f}A >= {current_threshold}A (possible mechanical jam)")
        except Exception:
            logger.debug(f"[{equipment_id}] Could not parse current sensor value: {sensors.get('current')}")

    # If any raw alerts found, send immediate notifications
    if alerts:
        alert_message = f"🚨 SENSOR THRESHOLD ALERT: {equipment.get('name', equipment_id)} ({equipment_id})\n"
        alert_message += f"Location: {equipment.get('location', 'Unknown')}\n"
        alert_message += f"Equipment Type: {equipment_type}\n\n"
        for a in alerts:
            alert_message += f"• {a}\n"
        alert_message += f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        for channel in equipment.get('alert_channels', ['discord']):
            try:
                if channel == 'discord':
                    alert_manager.send_discord_alert(alert_message)
                elif channel == 'email':
                    alert_manager.send_email_alert(f"Sensor Threshold Alert: {equipment.get('name', equipment_id)}", alert_message)
                elif channel == 'sms':
                    logger.warning(f"SMS alerts not implemented yet for {equipment_id}")
            except Exception as e:
                logger.error(f"[{equipment_id}] Failed to send sensor threshold alert via {channel}: {e}")

        logger.warning(f"[{equipment_id}] Sensor threshold alert sent: {len(alerts)} issues")

# ============================================================================
# MAIN MONITORING LOOP
# ============================================================================

def monitor_equipment(equipment: Dict[str, Any]):
    """
    Monitor a single equipment unit (one iteration).
    """
    equipment_id = equipment["id"]
    
    # Read all sensors
    readings = read_equipment_sensors(equipment)

    # Security monitoring (motion, tampering, after-hours activity)
    try:
        security_monitor.monitor_security(equipment, readings)
    except Exception as e:
        logger.error(f"[{equipment_id}] Error in security monitoring: {e}")

    # Quick raw sensor threshold checks (fire, gas, CO2, oxygen, fridge temps)
    try:
        check_raw_sensor_thresholds(equipment, readings)
    except Exception as e:
        logger.error(f"[{equipment_id}] Error in raw sensor threshold checks: {e}")
    
    # Run AI inference on sensor data
    inference_results = []
    
    # Thermal inference
    if "thermal" in readings["sensors"]:
        thermal_result = run_thermal_inference(readings["sensors"]["thermal"], equipment_id)
        inference_results.append(thermal_result)
    
    # Acoustic inference
    if "audio" in readings["sensors"]:
        acoustic_result = run_acoustic_inference(readings["sensors"]["audio"], equipment_id)
        inference_results.append(acoustic_result)
    
    # LSTM inference (requires time-series buffer)
    if equipment_id not in equipment_lstm_buffers:
        equipment_lstm_buffers[equipment_id] = []

    # Build deterministic feature vector
    try:
        feature_vector = build_lstm_feature_vector(readings, equipment["type"])
        equipment_lstm_buffers[equipment_id].append(feature_vector)

        # Keep only last 50 time steps
        if len(equipment_lstm_buffers[equipment_id]) > 50:
            equipment_lstm_buffers[equipment_id].pop(0)

        # Run LSTM if we have enough data
        if len(equipment_lstm_buffers[equipment_id]) >= 50:
            buffer_array = np.array(equipment_lstm_buffers[equipment_id])  # Shape: (50, n_features)

            # Validate shape matches LSTM model input
            lstm_result = run_lstm_inference(buffer_array, equipment_id)
            inference_results.append(lstm_result)
    except Exception as e:
        logger.error(f"[{equipment_id}] Error building LSTM feature vector: {e}")
    
    # Check for anomalies and send alerts
    check_anomaly_and_alert(equipment, inference_results)
    
    # Store equipment state
    equipment_states[equipment_id] = {
        "last_reading": readings,
        "last_inference": inference_results,
        "timestamp": datetime.now().isoformat()
    }

def main_loop():
    """
    Main monitoring loop for all equipment assigned to this Pi.
    """
    # Get this Pi's ID and assigned equipment
    pi_id = equipment_registry.get_pi_id()
    equipment_list = equipment_registry.get_equipment_by_pi(pi_id)
    
    if not equipment_list:
        logger.error(f"No equipment assigned to Pi: {pi_id}")
        return
    
    logger.info(f"Starting monitoring for Pi: {pi_id}")
    logger.info(f"Monitoring {len(equipment_list)} equipment units:")
    for eq in equipment_list:
        logger.info(f"  - {eq['id']}: {eq['name']} ({eq['type']})")
    
    # Get sensor read interval
    sensor_read_interval = getattr(config, 'SENSOR_READ_INTERVAL', 30)
    
    iteration_count = 0
    
    try:
        while True:
            iteration_count += 1
            loop_start = time.time()
            
            logger.info(f"--- Monitoring Cycle {iteration_count} ---")
            
            # Monitor each equipment unit
            for equipment in equipment_list:
                try:
                    monitor_equipment(equipment)
                except Exception as e:
                    logger.error(f"Error monitoring {equipment['id']}: {e}")
            
            # Calculate sleep time
            loop_duration = time.time() - loop_start
            sleep_time = max(0, sensor_read_interval - loop_duration)
            
            logger.info(f"Cycle complete. Loop took {loop_duration:.2f}s. Sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)
            
    except KeyboardInterrupt:
        logger.info("Monitoring stopped by user")
    except Exception as e:
        logger.critical(f"Critical error in main loop: {e}")
        raise

# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    logger.info("=" * 80)
    logger.info("PREMONITOR Multi-Equipment Monitoring System - STARTUP")
    logger.info("=" * 80)
    
    # Run startup checks
    if not startup_check():
        logger.critical("Startup checks failed. Please fix configuration issues.")
        sys.exit(1)
    
    logger.info("✓ Startup checks passed")
    
    # Load AI models
    if not load_models():
        logger.critical("Failed to load AI models. Exiting.")
        sys.exit(1)
    
    logger.info("✓ AI models loaded")
    
    # Initialize hardware
    try:
        hardware.init_hardware()
        logger.info("✓ Hardware initialized")
    except Exception as e:
        logger.error(f"Hardware initialization failed: {e}")
        logger.warning("Continuing anyway (may be using mock hardware)")
    
    # Start monitoring
    logger.info("=" * 80)
    logger.info("Starting main monitoring loop...")
    logger.info("=" * 80)
    
    try:
        main_loop()
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        sys.exit(1)
