# -*- coding: utf-8 -*-
"""
PREMONITOR Security Monitoring Module
Handles motion detection, tamper detection, after-hours monitoring, and activity logging.

Author: Alexandru Emanuel Vasile
License: BSD 3-Clause (see LICENSE)
"""

import time
import logging
import json
from datetime import datetime, time as dt_time
from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np

logger = logging.getLogger('security_monitor')

# ============================================================================
# SECURITY CONFIGURATION
# ============================================================================

SECURITY_CONFIG = {
    # After-hours schedule (when enhanced security is active)
    "business_hours": {
        "start": "08:00",  # 8 AM
        "end": "18:00",    # 6 PM
        "weekdays_only": True  # Enhanced security on weekends
    },

    # Motion detection settings
    "motion_detection": {
        "enabled": True,
        "sensitivity": 0.7,  # 0.0-1.0, higher = more sensitive
        "cooldown_seconds": 300,  # 5 minutes between motion alerts
        "capture_images": True,
        "capture_duration": 10  # Capture for 10 seconds after motion
    },

    # Tamper detection settings
    "tamper_detection": {
        "enabled": True,
        "vibration_threshold": 2.0,  # G-force (much higher than normal operation)
        "temperature_change_rate": 5.0,  # °C per minute (rapid change = tampering)
        "door_open_sensor": False  # Set to True if using magnetic door sensors
    },

    # Activity logging
    "activity_logging": {
        "enabled": True,
        "log_file": "../logs/security_activity.log",
        "log_all_access": True,  # Log all sensor reads, not just anomalies
        "retention_days": 90
    },

    # Intrusion response
    "intrusion_response": {
        "send_sms": True,  # Send SMS for high-priority security alerts
        "send_email": True,
        "send_discord": True,
        "capture_thermal_image": True,
        "capture_audio": False,  # Record audio if movement detected
        "lock_down_mode": False  # Prevent equipment operation until cleared
    }
}

# ============================================================================
# MOTION DETECTION
# ============================================================================

class MotionDetector:
    """
    PIR motion sensor integration for detecting unauthorized access.
    Compatible with HC-SR501 PIR sensor or similar.
    """

    def __init__(self, gpio_pin: int = 18):
        """
        Initialize motion detector.

        Args:
            gpio_pin: GPIO pin number for PIR sensor (default: GPIO 18)
        """
        self.gpio_pin = gpio_pin
        self.last_motion_time = None
        self.motion_active = False

        try:
            import RPi.GPIO as GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.gpio_pin, GPIO.IN)
            self.gpio_available = True
            logger.info(f"Motion detector initialized on GPIO {gpio_pin}")
        except ImportError:
            self.gpio_available = False
            logger.warning("RPi.GPIO not available - motion detection will use mock data")

    def detect_motion(self) -> bool:
        """
        Check if motion is detected.

        Returns:
            True if motion detected, False otherwise
        """
        if not SECURITY_CONFIG["motion_detection"]["enabled"]:
            return False

        if self.gpio_available:
            import RPi.GPIO as GPIO
            motion = GPIO.input(self.gpio_pin) == GPIO.HIGH
        else:
            # Mock motion detection for testing
            import random
            motion = random.random() < 0.02  # 2% chance of "motion" for testing

        if motion and not self.motion_active:
            self.last_motion_time = datetime.now()
            self.motion_active = True
            logger.warning(f"MOTION DETECTED at {self.last_motion_time}")
            return True
        elif not motion and self.motion_active:
            self.motion_active = False

        return motion

    def is_cooldown_active(self) -> bool:
        """Check if motion detection is in cooldown period."""
        if self.last_motion_time is None:
            return False

        cooldown = SECURITY_CONFIG["motion_detection"]["cooldown_seconds"]
        elapsed = (datetime.now() - self.last_motion_time).total_seconds()
        return elapsed < cooldown


# ============================================================================
# TAMPER DETECTION
# ============================================================================

class TamperDetector:
    """
    Detect physical tampering with equipment using multiple sensor inputs.
    """

    def __init__(self):
        self.baseline_readings = {}
        self.tamper_events = []

    def check_tamper(self, equipment_id: str, readings: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """
        Check for tampering indicators.

        Args:
            equipment_id: Equipment identifier
            readings: Current sensor readings

        Returns:
            Dict with tamper details if detected, None otherwise
        """
        if not SECURITY_CONFIG["tamper_detection"]["enabled"]:
            return None

        sensors = readings.get("sensors", {})

        # Check 1: Abnormal vibration (equipment being moved/hit)
        if "vibration" in sensors:
            vib_val = float(sensors["vibration"])
            threshold = SECURITY_CONFIG["tamper_detection"]["vibration_threshold"]
            if vib_val >= threshold:
                return {
                    "type": "physical_tampering",
                    "indicator": "abnormal_vibration",
                    "value": f"{vib_val:.2f}G",
                    "message": f"Equipment experienced {vib_val:.2f}G vibration (possible physical tampering)"
                }

        # Check 2: Rapid temperature change (door left open or equipment disabled)
        if equipment_id in self.baseline_readings and "temperature" in sensors:
            prev_temp = self.baseline_readings[equipment_id].get("temperature")
            prev_time = self.baseline_readings[equipment_id].get("timestamp")

            if prev_temp is not None and prev_time is not None:
                current_temp = float(sensors["temperature"])
                time_diff = (datetime.now() - prev_time).total_seconds() / 60.0  # minutes

                if time_diff > 0:
                    temp_change_rate = abs(current_temp - prev_temp) / time_diff
                    max_rate = SECURITY_CONFIG["tamper_detection"]["temperature_change_rate"]

                    if temp_change_rate > max_rate:
                        return {
                            "type": "thermal_tampering",
                            "indicator": "rapid_temperature_change",
                            "value": f"{temp_change_rate:.2f}°C/min",
                            "message": f"Temperature changing at {temp_change_rate:.2f}°C/min (possible door open/tampering)"
                        }

        # Update baseline readings
        self.baseline_readings[equipment_id] = {
            "temperature": sensors.get("temperature"),
            "timestamp": datetime.now()
        }

        return None


# ============================================================================
# AFTER-HOURS MONITORING
# ============================================================================

def is_after_hours() -> bool:
    """
    Check if current time is outside business hours.

    Returns:
        True if after-hours (enhanced security), False if business hours
    """
    now = datetime.now()
    config = SECURITY_CONFIG["business_hours"]

    # Check weekends
    if config["weekdays_only"] and now.weekday() >= 5:  # Saturday=5, Sunday=6
        return True

    # Parse business hours
    try:
        start_time = datetime.strptime(config["start"], "%H:%M").time()
        end_time = datetime.strptime(config["end"], "%H:%M").time()
        current_time = now.time()

        return not (start_time <= current_time <= end_time)
    except Exception as e:
        logger.error(f"Error parsing business hours: {e}")
        return False


# ============================================================================
# CAMERA CAPTURE ON MOTION
# ============================================================================

def capture_thermal_image_on_motion(equipment_id: str, thermal_data: np.ndarray) -> Optional[str]:
    """
    Save thermal image when motion detected.

    Args:
        equipment_id: Equipment identifier
        thermal_data: Thermal camera data array

    Returns:
        Path to saved image, or None if capture failed
    """
    if not SECURITY_CONFIG["motion_detection"]["capture_images"]:
        return None

    try:
        from PIL import Image

        # Create security captures directory
        capture_dir = Path("../logs/security_captures")
        capture_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = capture_dir / f"motion_{equipment_id}_{timestamp}.png"

        # Convert thermal data to image
        if thermal_data.shape[-1] == 3:  # RGB thermal image
            img = Image.fromarray(thermal_data.astype(np.uint8))
        else:  # Grayscale thermal
            img = Image.fromarray((thermal_data * 255).astype(np.uint8), mode='L')

        img.save(filename)
        logger.info(f"Captured thermal image on motion: {filename}")
        return str(filename)

    except Exception as e:
        logger.error(f"Failed to capture thermal image: {e}")
        return None


# ============================================================================
# ACTIVITY LOGGING
# ============================================================================

class ActivityLogger:
    """
    Log all equipment access and security events with timestamps.
    """

    def __init__(self):
        self.log_file = Path(SECURITY_CONFIG["activity_logging"]["log_file"])
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        # Set up JSON logging for structured data
        self.log_file_json = self.log_file.with_suffix('.json')

    def log_activity(self, event_type: str, equipment_id: str, details: Dict[str, Any]) -> None:
        """
        Log a security or access event.

        Args:
            event_type: Type of event (motion, tamper, access, etc.)
            equipment_id: Equipment identifier
            details: Additional event details
        """
        if not SECURITY_CONFIG["activity_logging"]["enabled"]:
            return

        timestamp = datetime.now()

        # Create structured log entry
        log_entry = {
            "timestamp": timestamp.isoformat(),
            "event_type": event_type,
            "equipment_id": equipment_id,
            "details": details,
            "after_hours": is_after_hours()
        }

        # Append to JSON log file
        try:
            with open(self.log_file_json, 'a') as f:
                json.dump(log_entry, f)
                f.write('\n')
        except Exception as e:
            logger.error(f"Failed to write to activity log: {e}")

        # Also write to standard log
        logger.info(f"ACTIVITY LOG [{event_type}] {equipment_id}: {details}")

    def get_recent_activity(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Retrieve recent activity logs.

        Args:
            hours: Number of hours to look back

        Returns:
            List of activity log entries
        """
        if not self.log_file_json.exists():
            return []

        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        recent_entries = []

        try:
            with open(self.log_file_json, 'r') as f:
                for line in f:
                    entry = json.loads(line)
                    entry_time = datetime.fromisoformat(entry["timestamp"]).timestamp()
                    if entry_time >= cutoff_time:
                        recent_entries.append(entry)
        except Exception as e:
            logger.error(f"Failed to read activity log: {e}")

        return recent_entries


# ============================================================================
# INTRUSION ALERT
# ============================================================================

def send_intrusion_alert(equipment_id: str, alert_type: str, details: Dict[str, Any],
                         thermal_image_path: Optional[str] = None) -> None:
    """
    Send high-priority security alert via multiple channels.

    Args:
        equipment_id: Equipment identifier
        alert_type: Type of intrusion (motion, tamper, etc.)
        details: Alert details
        thermal_image_path: Optional path to captured thermal image
    """
    import alert_manager

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    after_hours = is_after_hours()

    # Build alert message
    alert_message = f"🚨🚨 SECURITY ALERT 🚨🚨\n"
    alert_message += f"Type: {alert_type.upper()}\n"
    alert_message += f"Equipment: {equipment_id}\n"
    alert_message += f"Time: {timestamp}\n"
    alert_message += f"Status: {'AFTER HOURS' if after_hours else 'BUSINESS HOURS'}\n"
    alert_message += f"\nDetails:\n"

    for key, value in details.items():
        alert_message += f"  • {key}: {value}\n"

    if thermal_image_path:
        alert_message += f"\nThermal image captured: {thermal_image_path}\n"

    alert_message += f"\n⚠️ IMMEDIATE ACTION REQUIRED ⚠️"

    config = SECURITY_CONFIG["intrusion_response"]

    # Send via Discord
    if config["send_discord"]:
        try:
            alert_manager.send_discord_alert(alert_message)
        except Exception as e:
            logger.error(f"Failed to send Discord intrusion alert: {e}")

    # Send via Email
    if config["send_email"]:
        try:
            alert_manager.send_email_alert(
                subject=f"🚨 SECURITY ALERT - {equipment_id}",
                message=alert_message
            )
        except Exception as e:
            logger.error(f"Failed to send email intrusion alert: {e}")

    # Send via SMS (if configured)
    if config["send_sms"]:
        try:
            sms_message = f"SECURITY ALERT: {alert_type} detected at {equipment_id}. Time: {timestamp}. Check email for details."
            alert_manager.send_sms_alert(sms_message)
        except Exception as e:
            logger.error(f"Failed to send SMS intrusion alert: {e}")


# ============================================================================
# MAIN SECURITY MONITORING FUNCTION
# ============================================================================

# Global instances
motion_detector = None
tamper_detector = None
activity_logger = None

def initialize_security_monitoring():
    """Initialize all security monitoring components."""
    global motion_detector, tamper_detector, activity_logger

    motion_detector = MotionDetector()
    tamper_detector = TamperDetector()
    activity_logger = ActivityLogger()

    logger.info("Security monitoring initialized")


def monitor_security(equipment: Dict[str, Any], readings: Dict[str, Any]) -> None:
    """
    Main security monitoring function - call this from main monitoring loop.

    Args:
        equipment: Equipment configuration
        readings: Current sensor readings including thermal camera data
    """
    if motion_detector is None:
        initialize_security_monitoring()

    equipment_id = equipment["id"]
    after_hours = is_after_hours()

    # Enhanced monitoring during after-hours
    if after_hours or SECURITY_CONFIG["motion_detection"]["enabled"]:

        # Check for motion
        motion_detected = motion_detector.detect_motion()

        if motion_detected and not motion_detector.is_cooldown_active():
            # Log motion event
            activity_logger.log_activity(
                event_type="motion_detected",
                equipment_id=equipment_id,
                details={
                    "location": equipment.get("location", "Unknown"),
                    "after_hours": after_hours,
                    "thermal_data_available": "thermal" in readings.get("sensors", {})
                }
            )

            # Capture thermal image if motion detected
            thermal_image_path = None
            if "thermal" in readings.get("sensors", {}):
                thermal_data = readings["sensors"]["thermal"]
                thermal_image_path = capture_thermal_image_on_motion(equipment_id, thermal_data)

            # Send intrusion alert
            send_intrusion_alert(
                equipment_id=equipment_id,
                alert_type="unauthorized_motion",
                details={
                    "message": "Motion detected in equipment area",
                    "location": equipment.get("location", "Unknown"),
                    "after_hours": "YES" if after_hours else "NO",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                },
                thermal_image_path=thermal_image_path
            )

    # Check for tampering (always active)
    tamper_result = tamper_detector.check_tamper(equipment_id, readings)

    if tamper_result:
        # Log tamper event
        activity_logger.log_activity(
            event_type="tamper_detected",
            equipment_id=equipment_id,
            details=tamper_result
        )

        # Capture thermal image if available
        thermal_image_path = None
        if "thermal" in readings.get("sensors", {}):
            thermal_data = readings["sensors"]["thermal"]
            thermal_image_path = capture_thermal_image_on_motion(equipment_id, thermal_data)

        # Send intrusion alert
        send_intrusion_alert(
            equipment_id=equipment_id,
            alert_type="equipment_tampering",
            details=tamper_result,
            thermal_image_path=thermal_image_path
        )

    # Log routine access (if enabled)
    if SECURITY_CONFIG["activity_logging"]["log_all_access"]:
        activity_logger.log_activity(
            event_type="routine_monitoring",
            equipment_id=equipment_id,
            details={
                "sensors_read": list(readings.get("sensors", {}).keys()),
                "after_hours": after_hours
            }
        )


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_security_status() -> Dict[str, Any]:
    """
    Get current security monitoring status.

    Returns:
        Dictionary with security status information
    """
    return {
        "motion_detection_enabled": SECURITY_CONFIG["motion_detection"]["enabled"],
        "tamper_detection_enabled": SECURITY_CONFIG["tamper_detection"]["enabled"],
        "after_hours_mode": is_after_hours(),
        "activity_logging_enabled": SECURITY_CONFIG["activity_logging"]["enabled"],
        "last_motion": motion_detector.last_motion_time.isoformat() if motion_detector and motion_detector.last_motion_time else None
    }


def generate_security_report(hours: int = 24) -> str:
    """
    Generate security activity report for specified time period.

    Args:
        hours: Number of hours to include in report

    Returns:
        Formatted security report string
    """
    if activity_logger is None:
        return "Activity logger not initialized"

    activities = activity_logger.get_recent_activity(hours)

    report = f"SECURITY ACTIVITY REPORT - Last {hours} hours\n"
    report += "=" * 60 + "\n\n"

    # Count event types
    motion_events = sum(1 for a in activities if a["event_type"] == "motion_detected")
    tamper_events = sum(1 for a in activities if a["event_type"] == "tamper_detected")
    total_events = len(activities)

    report += f"Summary:\n"
    report += f"  Total Events: {total_events}\n"
    report += f"  Motion Detected: {motion_events}\n"
    report += f"  Tampering Detected: {tamper_events}\n"
    report += f"  Routine Monitoring: {total_events - motion_events - tamper_events}\n\n"

    if motion_events > 0 or tamper_events > 0:
        report += "Security Events:\n"
        for activity in activities:
            if activity["event_type"] in ["motion_detected", "tamper_detected"]:
                report += f"  [{activity['timestamp']}] {activity['event_type'].upper()}\n"
                report += f"    Equipment: {activity['equipment_id']}\n"
                report += f"    Details: {activity['details']}\n\n"

    return report


if __name__ == "__main__":
    # Test security monitoring
    print("Testing PREMONITOR Security Monitoring...")

    initialize_security_monitoring()

    print(f"\nCurrent Status:")
    print(f"  After Hours: {is_after_hours()}")
    print(f"  Motion Detection: {'Enabled' if SECURITY_CONFIG['motion_detection']['enabled'] else 'Disabled'}")
    print(f"  Tamper Detection: {'Enabled' if SECURITY_CONFIG['tamper_detection']['enabled'] else 'Disabled'}")

    print("\nSecurity monitoring initialized successfully!")
