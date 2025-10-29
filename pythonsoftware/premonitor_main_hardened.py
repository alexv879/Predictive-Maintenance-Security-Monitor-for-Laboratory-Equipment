#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Premonitor: main.py (Hardened Version)
This is the main entry point for the Premonitor application with production improvements:
- Structured logging instead of prints
- TFLite runtime fallback (tflite_runtime → tensorflow)
- Robust shape/dtype handling for quantized models
- Startup validation checks
- Graceful error handling

Author: PREMONITOR Team
Version: 2.0 (Hardened)
"""

import time
import sys
import os
import signal
import logging
from pathlib import Path
from datetime import datetime
import numpy as np

# Try importing tflite_runtime first (lighter weight for Pi), fall back to tensorflow
try:
    from tflite_runtime.interpreter import Interpreter as TFLiteInterpreter
    TFLITE_RUNTIME_AVAILABLE = True
    logging.info("Using tflite_runtime for model inference")
except ImportError:
    try:
        import tensorflow as tf
        TFLiteInterpreter = tf.lite.Interpreter
        TFLITE_RUNTIME_AVAILABLE = False
        logging.info("Using tensorflow.lite for model inference")
    except ImportError:
        logging.critical("Neither tflite_runtime nor tensorflow available. Cannot run.")
        sys.exit(1)

# Add pythonsoftware to path
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

# Import custom modules
try:
    import premonitor_config_py as config
    import premonitor_alert_manager_py as alert_manager
    import premonitor_mock_hardware_py as hardware
except ImportError as e:
    logging.critical(f"Failed to import required modules: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if getattr(config, 'DEBUG_MODE', True) else logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(config.LOG_DIR / 'premonitor_main.log' if hasattr(config, 'LOG_DIR') else 'premonitor_main.log')
    ]
)

logger = logging.getLogger('premonitor.main')

# Global variables for loaded AI models
thermal_interpreter = None
acoustic_interpreter = None

# Shutdown flag
shutdown_requested = False


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global shutdown_requested
    logger.info(f"Received signal {signum}. Initiating graceful shutdown...")
    shutdown_requested = True


def startup_check():
    """
    Perform startup validation checks before running main loop.
    Returns: (success: bool, errors: list)
    """
    errors = []
    logger.info("Running startup validation checks...")

    # Check model paths
    if not hasattr(config, 'THERMAL_MODEL_PATH') or not Path(config.THERMAL_MODEL_PATH).exists():
        errors.append(f"Thermal model not found: {getattr(config, 'THERMAL_MODEL_PATH', 'NOT_CONFIGURED')}")
    
    if not hasattr(config, 'ACOUSTIC_MODEL_PATH') or not Path(config.ACOUSTIC_MODEL_PATH).exists():
        errors.append(f"Acoustic model not found: {getattr(config, 'ACOUSTIC_MODEL_PATH', 'NOT_CONFIGURED')}")

    # Check required config values
    required_configs = [
        'SENSOR_READ_INTERVAL',
        'THERMAL_ANOMALY_CONFIDENCE',
        'ACOUSTIC_ANOMALY_CONFIDENCE',
        'FUSION_CORRELATION_CONFIDENCE',
        'GAS_ANALOG_THRESHOLD'
    ]
    
    for cfg in required_configs:
        if not hasattr(config, cfg):
            errors.append(f"Missing config value: {cfg}")

    # Check directories
    if hasattr(config, 'LOG_DIR'):
        Path(config.LOG_DIR).mkdir(parents=True, exist_ok=True)
    
    if hasattr(config, 'CAPTURE_DIR'):
        Path(config.CAPTURE_DIR).mkdir(parents=True, exist_ok=True)

    if errors:
        logger.error("Startup validation failed:")
        for error in errors:
            logger.error(f"  - {error}")
        return False, errors
    
    logger.info("Startup validation passed ✓")
    return True, []


def load_models():
    """
    Loads the trained and quantized .tflite models into memory.
    Uses TFLiteInterpreter (either tflite_runtime or tensorflow.lite).
    Raises RuntimeError if models cannot be loaded.
    """
    global thermal_interpreter, acoustic_interpreter
    logger.info("Loading AI models...")
    
    try:
        # Load thermal model
        logger.debug(f"Loading thermal model from: {config.THERMAL_MODEL_PATH}")
        thermal_interpreter = TFLiteInterpreter(model_path=config.THERMAL_MODEL_PATH)
        thermal_interpreter.allocate_tensors()
        
        # Log model details
        input_details = thermal_interpreter.get_input_details()
        output_details = thermal_interpreter.get_output_details()
        logger.info(f"Thermal model loaded: input={input_details[0]['shape']}, output={output_details[0]['shape']}, dtype={input_details[0]['dtype']}")
        
        # Load acoustic model
        logger.debug(f"Loading acoustic model from: {config.ACOUSTIC_MODEL_PATH}")
        acoustic_interpreter = TFLiteInterpreter(model_path=config.ACOUSTIC_MODEL_PATH)
        acoustic_interpreter.allocate_tensors()
        
        input_details = acoustic_interpreter.get_input_details()
        output_details = acoustic_interpreter.get_output_details()
        logger.info(f"Acoustic model loaded: input={input_details[0]['shape']}, output={output_details[0]['shape']}, dtype={input_details[0]['dtype']}")
        
        logger.info("All models loaded successfully ✓")
        
    except Exception as e:
        logger.error(f"CRITICAL: Failed to load models: {e}", exc_info=True)
        raise RuntimeError(f"Model loading failed: {e}")


def normalize_shape(shape):
    """Normalize shape array to tuple of integers, handling -1 and None."""
    return tuple(int(x) if x not in (-1, None) else -1 for x in shape)


def run_inference(interpreter, input_data):
    """
    Run inference on a loaded TFLite interpreter with robust shape/dtype handling.
    
    Args:
        interpreter: TFLite interpreter instance
        input_data: numpy array of input data
    
    Returns:
        float: Anomaly score (0.0-1.0) or None if inference fails
    """
    if interpreter is None:
        logger.warning("Interpreter is None, returning default score")
        return 0.0
    
    try:
        input_details = interpreter.get_input_details()[0]
        output_details = interpreter.get_output_details()[0]
        
        # Normalize expected shape (ignore batch dimension)
        expected_shape = normalize_shape(input_details['shape'][1:])
        input_shape = input_data.shape
        
        # Check shape compatibility (allow for flexible dimensions marked as -1)
        if not all(exp == -1 or exp == inp for exp, inp in zip(expected_shape, input_shape)):
            logger.warning(f"Input shape mismatch: got {input_shape}, expected {expected_shape}")
            return 0.0
        
        # Prepare input tensor with correct dtype
        input_dtype = input_details['dtype']
        
        if input_dtype == np.uint8:
            # Quantized model - scale float input to uint8
            input_tensor = np.expand_dims(input_data, axis=0)
            input_tensor = (np.clip(input_tensor, 0, 1) * 255).astype(np.uint8)
            logger.debug("Using quantized (uint8) input")
        elif input_dtype == np.int8:
            # INT8 quantized model
            scale, zero_point = input_details['quantization']
            input_tensor = np.expand_dims(input_data, axis=0)
            input_tensor = ((input_tensor / scale) + zero_point).astype(np.int8)
            logger.debug("Using INT8 quantized input")
        else:
            # Float32 model
            input_tensor = np.expand_dims(input_data, axis=0).astype(np.float32)
            logger.debug("Using float32 input")
        
        # Run inference
        interpreter.set_tensor(input_details['index'], input_tensor)
        interpreter.invoke()
        prediction = interpreter.get_tensor(output_details['index'])
        
        # Handle output dtype
        output_dtype = output_details['dtype']
        if output_dtype in (np.uint8, np.int8):
            # Dequantize output
            scale, zero_point = output_details['quantization']
            prediction = (prediction.astype(np.float32) - zero_point) * scale
            logger.debug(f"Dequantized output: scale={scale}, zero_point={zero_point}")
        
        # Extract scalar score
        score = float(np.ravel(prediction)[0])
        score = np.clip(score, 0.0, 1.0)  # Ensure in valid range
        
        return score
        
    except Exception as e:
        logger.error(f"Inference error: {e}", exc_info=True)
        return 0.0


def main():
    """
    Main orchestration function for the Premonitor system.
    """
    global shutdown_requested
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("=" * 60)
    logger.info("PREMONITOR SYSTEM STARTING (Hardened v2.0)")
    logger.info("=" * 60)
    
    # Startup validation
    success, errors = startup_check()
    if not success:
        logger.critical("Startup validation failed. Cannot continue.")
        return 1
    
    # Load models
    try:
        load_models()
    except RuntimeError as e:
        logger.critical(f"Cannot run without models: {e}")
        return 1
    
    # Initialize hardware
    try:
        logger.info("Initializing hardware (mock mode)...")
        hardware.initialize_mock_data()
        logger.info("Hardware initialized ✓")
    except Exception as e:
        logger.error(f"Hardware initialization failed: {e}", exc_info=True)
        return 1
    
    # Main monitoring loop
    logger.info("Starting main monitoring loop...")
    cycle_count = 0
    
    while not shutdown_requested:
        try:
            cycle_count += 1
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"--- Cycle {cycle_count} at {current_time} ---")
            
            # 1. Read sensors
            logger.debug("Reading sensors...")
            thermal_image = hardware.read_thermal_image()
            acoustic_spectrogram = hardware.read_acoustic_spectrogram()
            gas_reading = hardware.read_gas_sensor()
            
            # Validate sensor data
            if thermal_image is None or acoustic_spectrogram is None:
                logger.warning("Invalid sensor data received, skipping cycle")
                time.sleep(config.SENSOR_READ_INTERVAL)
                continue
            
            # 2. Run AI inference
            logger.debug("Running inference...")
            thermal_score = run_inference(thermal_interpreter, thermal_image)
            acoustic_score = run_inference(acoustic_interpreter, acoustic_spectrogram)
            
            logger.info(f"Scores: Thermal={thermal_score:.3f}, Acoustic={acoustic_score:.3f}, Gas={gas_reading}")
            
            # 3. Apply sensor fusion & alerting logic
            alert_triggered = False
            
            # Case 1: High-confidence single-sensor alert (critical)
            if thermal_score > config.THERMAL_ANOMALY_CONFIDENCE:
                logger.warning(f"CRITICAL thermal anomaly detected: {thermal_score:.3f}")
                details = f"Critical thermal anomaly detected with confidence {thermal_score:.3f}"
                alert_manager.send_alert_in_background("CRITICAL: High-Confidence Thermal Anomaly", details)
                alert_triggered = True
            
            elif acoustic_score > config.ACOUSTIC_ANOMALY_CONFIDENCE:
                logger.warning(f"CRITICAL acoustic anomaly detected: {acoustic_score:.3f}")
                details = f"Critical acoustic anomaly detected with confidence {acoustic_score:.3f}"
                alert_manager.send_alert_in_background("CRITICAL: High-Confidence Acoustic Anomaly", details)
                alert_triggered = True
            
            # Case 2: Correlated multi-sensor alert (proactive)
            elif (thermal_score > config.FUSION_CORRELATION_CONFIDENCE and 
                  acoustic_score > config.FUSION_CORRELATION_CONFIDENCE):
                logger.warning(f"Correlated anomaly: thermal={thermal_score:.3f}, acoustic={acoustic_score:.3f}")
                details = (f"Potential issue detected by correlating weak signals:\n"
                          f"- Thermal: {thermal_score:.3f} (threshold: {config.FUSION_CORRELATION_CONFIDENCE})\n"
                          f"- Acoustic: {acoustic_score:.3f} (threshold: {config.FUSION_CORRELATION_CONFIDENCE})")
                alert_manager.send_alert_in_background("WARNING: Correlated Anomaly Detected", details)
                alert_triggered = True
            
            # Case 3: Simple threshold alert for basic sensors
            if gas_reading > config.GAS_ANALOG_THRESHOLD:
                logger.warning(f"High gas level detected: {gas_reading}")
                details = f"Gas sensor reading {gas_reading} exceeds threshold {config.GAS_ANALOG_THRESHOLD}"
                alert_manager.send_alert_in_background("WARNING: High Gas Level Detected", details)
                alert_triggered = True
            
            if not alert_triggered:
                logger.debug("No anomalies detected, system normal")
            
            # 4. Wait for next cycle
            time.sleep(config.SENSOR_READ_INTERVAL)
            
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
            shutdown_requested = True
            break
            
        except Exception as e:
            logger.error(f"Unhandled error in main loop: {e}", exc_info=True)
            logger.info("Waiting 30s before retry to avoid error spam...")
            time.sleep(30)
    
    logger.info("=" * 60)
    logger.info("PREMONITOR SYSTEM SHUTDOWN COMPLETE")
    logger.info(f"Total cycles completed: {cycle_count}")
    logger.info("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
