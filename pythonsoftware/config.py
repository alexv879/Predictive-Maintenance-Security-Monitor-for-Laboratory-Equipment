# -*- coding: utf-8 -*-
"""
PREMONITOR Configuration Module
Contains all configuration settings, path management, and logging setup.
"""

import os
import json
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Dict, Any, Tuple, List
import sys

# =============================================================================
# GENERAL SETTINGS
# =============================================================================

# Debug mode - enables detailed logging
DEBUG_MODE = os.environ.get("PREMONITOR_DEBUG", "False").lower() == "true"

# Sensor reading interval in seconds
SENSOR_READ_INTERVAL = float(os.environ.get("PREMONITOR_SENSOR_INTERVAL", "30.0"))

# =============================================================================
# FILE PATHS
# =============================================================================

# Base directory - use environment variable or fallback to script location
BASE_DIR = Path(os.environ.get("PREMONITOR_BASE_DIR", os.path.dirname(os.path.abspath(__file__))))

# Model directory
MODEL_DIR = Path(os.environ.get("PREMONITOR_MODEL_DIR", BASE_DIR.parent / "models"))

# Model file paths - now correctly pointing to parent/models directory
THERMAL_MODEL_PATH = MODEL_DIR / os.environ.get("THERMAL_MODEL_NAME", "thermal_anomaly_model_int8.tflite")
ACOUSTIC_MODEL_PATH = MODEL_DIR / os.environ.get("ACOUSTIC_MODEL_NAME", "acoustic_anomaly_model_int8.tflite")
LSTM_MODEL_PATH = MODEL_DIR / os.environ.get("LSTM_MODEL_NAME", "lstm_autoencoder_model.tflite")
LSTM_AE_MODEL_PATH = LSTM_MODEL_PATH  # Alias for compatibility

# Logging and capture directories
LOG_DIR = Path(os.environ.get("PREMONITOR_LOG_DIR", BASE_DIR.parent / "logs"))
CAPTURE_DIR = Path(os.environ.get("PREMONITOR_CAPTURE_DIR", BASE_DIR.parent / "captures"))

# Ensure directories exist
for directory in [LOG_DIR, CAPTURE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Device-specific configuration file
DEVICE_CONFIG_FILE = BASE_DIR.parent / "device_config.json"

# =============================================================================
# SENSOR THRESHOLDS & PARAMETERS
# =============================================================================

# Simple threshold for critical temperature
THERMAL_CRITICAL_THRESHOLD_C = 75.0  # Celsius

# Gas sensor threshold (must be calibrated for specific sensor)
GAS_ANALOG_THRESHOLD = 600

# =============================================================================
# AI MODEL PARAMETERS
# =============================================================================

# Input shapes for models
THERMAL_MODEL_INPUT_SHAPE = (224, 224, 3)
ACOUSTIC_MODEL_INPUT_SHAPE = (128, 128, 1)

# Spectrogram settings for acoustic model
SPECTROGRAM_SAMPLE_RATE = 16000
SPECTROGRAM_N_MELS = 128
SPECTROGRAM_HOP_LENGTH = 512

# Confidence thresholds for AI models
THERMAL_ANOMALY_CONFIDENCE = 0.80
ACOUSTIC_ANOMALY_CONFIDENCE = 0.75

# Fusion logic threshold
FUSION_CORRELATION_CONFIDENCE = 0.60

# =============================================================================
# ALERTING CONFIGURATION
# =============================================================================

# Email configuration (from environment variables)
EMAIL_SENDER_ADDRESS = os.environ.get("EMAIL_SENDER_ADDRESS", None)
EMAIL_SENDER_PASSWORD = os.environ.get("EMAIL_SENDER_PASSWORD", None)
DEFAULT_EMAIL_RECIPIENT = os.environ.get("DEFAULT_EMAIL_RECIPIENT", "default_recipient@example.com")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Twilio SMS configuration
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", None)
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", None)
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER", None)

# Discord webhook configuration
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", None)

# Default SMS recipient
DEFAULT_SMS_RECIPIENT = os.environ.get("DEFAULT_SMS_RECIPIENT", None)

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

def setup_logging(log_level: str = None, log_file: str = None):
    """
    Configure structured logging with file rotation.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path (creates rotating handler)
    """
    level = getattr(logging, log_level or os.environ.get("PREMONITOR_LOG_LEVEL", "INFO"))

    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)8s] %(name)20s:%(lineno)4d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    simple_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S'
    )

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(simple_formatter if level >= logging.INFO else detailed_formatter)
    root_logger.addHandler(console_handler)

    # File handler with rotation (10MB max, keep 5 backups)
    if log_file or LOG_DIR:
        log_path = Path(log_file) if log_file else LOG_DIR / "premonitor.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)  # Always log DEBUG to file
        file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(file_handler)

        logging.info(f"Logging to file: {log_path}")

    # Reduce noise from verbose libraries
    logging.getLogger('tensorflow').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)


# =============================================================================
# CONFIGURATION VALIDATION
# =============================================================================

def validate_config() -> Tuple[bool, List[str]]:
    """
    Validate configuration and check for missing required settings.

    Returns:
        (is_valid, list_of_errors)
    """
    errors = []

    # Check model paths exist
    if not THERMAL_MODEL_PATH.exists():
        errors.append(f"WARNING: Thermal model not found: {THERMAL_MODEL_PATH}")
    if not ACOUSTIC_MODEL_PATH.exists():
        errors.append(f"WARNING: Acoustic model not found: {ACOUSTIC_MODEL_PATH}")

    # Check alert credentials (warnings only)
    if not EMAIL_SENDER_ADDRESS:
        errors.append("WARNING: EMAIL_SENDER_ADDRESS not configured")
    if not EMAIL_SENDER_PASSWORD:
        errors.append("WARNING: EMAIL_SENDER_PASSWORD not configured")

    # Count critical errors (non-WARNING)
    critical_errors = [e for e in errors if not e.startswith("WARNING")]

    return (len(critical_errors) == 0, errors)


# =============================================================================
# DEVICE CONFIGURATION SUPPORT
# =============================================================================

def load_device_config() -> Dict[str, Any]:
    """
    Load device-specific configuration from JSON file.
    Overrides default settings with device-specific values.

    Returns:
        Device configuration dictionary
    """
    logger = logging.getLogger('config')

    if not DEVICE_CONFIG_FILE.exists():
        logger.info(f"No device config file found at {DEVICE_CONFIG_FILE}")
        return {}

    try:
        with open(DEVICE_CONFIG_FILE, 'r') as f:
            device_config = json.load(f)

        logger.info(f"Loaded device config from {DEVICE_CONFIG_FILE}")
        return device_config
    except Exception as e:
        logger.error(f"Failed to load device config: {e}")
        return {}


def apply_device_config(device_config: Dict[str, Any]):
    """
    Apply device-specific configuration overrides.

    Args:
        device_config: Dictionary of configuration overrides
    """
    global SENSOR_READ_INTERVAL, THERMAL_ANOMALY_CONFIDENCE
    global ACOUSTIC_ANOMALY_CONFIDENCE, GAS_ANALOG_THRESHOLD

    logger = logging.getLogger('config')

    # Override sensor interval if specified
    if 'sensor_read_interval' in device_config:
        SENSOR_READ_INTERVAL = float(device_config['sensor_read_interval'])
        logger.info(f"Override: SENSOR_READ_INTERVAL = {SENSOR_READ_INTERVAL}")

    # Override thresholds if specified
    if 'thermal_threshold' in device_config:
        THERMAL_ANOMALY_CONFIDENCE = float(device_config['thermal_threshold'])
        logger.info(f"Override: THERMAL_ANOMALY_CONFIDENCE = {THERMAL_ANOMALY_CONFIDENCE}")

    if 'acoustic_threshold' in device_config:
        ACOUSTIC_ANOMALY_CONFIDENCE = float(device_config['acoustic_threshold'])
        logger.info(f"Override: ACOUSTIC_ANOMALY_CONFIDENCE = {ACOUSTIC_ANOMALY_CONFIDENCE}")

    if 'gas_threshold' in device_config:
        GAS_ANALOG_THRESHOLD = int(device_config['gas_threshold'])
        logger.info(f"Override: GAS_ANALOG_THRESHOLD = {GAS_ANALOG_THRESHOLD}")


# =============================================================================
# INITIALIZATION
# =============================================================================

# Print basic config info on import
print(f"PREMONITOR Config loaded - BASE_DIR: {BASE_DIR}")
print(f"  Models: {MODEL_DIR}")
print(f"  Logs: {LOG_DIR}")

# Validate configuration if enabled
if os.environ.get("PREMONITOR_VALIDATE_ON_IMPORT", "true").lower() == "true":
    is_valid, validation_errors = validate_config()
    if validation_errors:
        print("Configuration warnings:")
        for error in validation_errors:
            print(f"  - {error}")

# Auto-load device config if enabled
if os.environ.get("PREMONITOR_AUTO_LOAD_DEVICE_CONFIG", "true").lower() == "true":
    _device_cfg = load_device_config()
    if _device_cfg:
        # Note: This will only apply after logging is set up
        pass  # Will be applied in main script after logging setup
