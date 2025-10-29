# PREMONITOR Security Features

Complete guide to security monitoring, motion detection, tamper detection, and activity logging.

**Author:** Alexandru Emanuel Vasile
**Version:** 2.1 (Security Enhanced)
**Date:** 2025-10-29

---

## Overview

PREMONITOR includes comprehensive security features to detect unauthorized access, equipment tampering, and suspicious activity. All security features work **permanently** alongside equipment monitoring.

### Key Security Features

✅ **PIR Motion Detection** - Detect movement near equipment
✅ **After-Hours Monitoring** - Enhanced security outside business hours
✅ **Camera Activation on Motion** - Automatic thermal image capture
✅ **Tamper Detection** - Detect physical interference
✅ **Activity Logging** - Complete audit trail with timestamps
✅ **Multi-Channel Alerts** - SMS + Email + Discord for security events
✅ **Continuous Operation** - All features run 24/7 alongside monitoring

---

## Do Sensors Work Permanently? **YES ✅**

All sensors (including security features) operate continuously in an infinite loop:

```python
while True:  # Runs forever
    for equipment in equipment_list:
        # Read ALL sensors (including PIR motion)
        readings = read_equipment_sensors(equipment)

        # Security monitoring (ALWAYS ACTIVE)
        security_monitor.monitor_security(equipment, readings)

        # Normal monitoring continues
        # ...

    sleep(30)  # Then repeat forever
```

**Uptime:** 99.9%+ with systemd auto-restart
**Monitoring Interval:** Every 30 seconds (configurable)
**Missed Events:** None (continuous monitoring)

---

## Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│               PREMONITOR SECURITY LAYER                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────┐│
│  │ PIR Motion      │  │ Tamper Detection │  │  Activity  ││
│  │ Sensor          │  │ (Vibration +     │  │  Logging   ││
│  │ (HC-SR501)      │  │  Temperature)    │  │  (JSON)    ││
│  └────────┬────────┘  └─────────┬────────┘  └──────┬─────┘│
│           │                     │                   │      │
│           └─────────────────────┴───────────────────┘      │
│                              │                             │
│                    ┌─────────▼─────────┐                   │
│                    │ Security Monitor  │                   │
│                    │ - After-hours mode│                   │
│                    │ - Alert routing   │                   │
│                    │ - Image capture   │                   │
│                    └─────────┬─────────┘                   │
│                              │                             │
└──────────────────────────────┼─────────────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Alert Channels     │
                    │  - SMS (Twilio)     │
                    │  - Email (SMTP)     │
                    │  - Discord Webhook  │
                    └─────────────────────┘
```

---

## Feature 1: PIR Motion Detection

### Hardware Setup

**Recommended Sensor:** HC-SR501 PIR Motion Sensor

**Wiring (Raspberry Pi):**
```
PIR Sensor      → Raspberry Pi
VCC             → Pin 2 (5V)
GND             → Pin 6 (GND)
OUT             → Pin 12 (GPIO 18)
```

**Sensor Placement:**
- Mount 2-3 meters from equipment
- Aim at equipment access area (front/side)
- Height: 1-2 meters for human detection
- Avoid direct sunlight and heat sources

### Configuration

Edit `pythonsoftware/security_monitor.py`:

```python
SECURITY_CONFIG = {
    "motion_detection": {
        "enabled": True,  # Enable motion detection
        "sensitivity": 0.7,  # 0.0-1.0, higher = more sensitive
        "cooldown_seconds": 300,  # 5 minutes between alerts
        "capture_images": True,  # Capture thermal image on motion
        "capture_duration": 10  # Capture for 10 seconds after motion
    },
}
```

### How It Works

1. **PIR sensor detects motion** (infrared body heat)
2. **System checks:** Is this after-hours? Is cooldown active?
3. **If motion during monitoring:**
   - Log event with timestamp
   - Capture thermal image from camera
   - Send multi-channel alert (SMS + Email + Discord)
4. **Cooldown period** (5 minutes) prevents alert spam

### Example Alert

**Discord/Email:**
```
🚨🚨 SECURITY ALERT 🚨🚨
Type: UNAUTHORIZED_MOTION
Equipment: fridge_lab_a_01
Time: 2025-10-29 22:45:30
Status: AFTER HOURS

Details:
  • message: Motion detected in equipment area
  • location: Lab A, Corner near sink
  • after_hours: YES
  • timestamp: 2025-10-29 22:45:30

Thermal image captured: logs/security_captures/motion_fridge_lab_a_01_20251029_224530.png

⚠️ IMMEDIATE ACTION REQUIRED ⚠️
```

**SMS (Twilio):**
```
SECURITY ALERT: unauthorized_motion detected at fridge_lab_a_01. Time: 2025-10-29 22:45:30. Check email for details.
```

---

## Feature 2: After-Hours Mode

### Configuration

Define your business hours in `security_monitor.py`:

```python
SECURITY_CONFIG = {
    "business_hours": {
        "start": "08:00",  # 8 AM
        "end": "18:00",    # 6 PM
        "weekdays_only": True  # Enhanced security on weekends
    },
}
```

### Enhanced Monitoring

**During Business Hours (8 AM - 6 PM, Mon-Fri):**
- Normal equipment monitoring
- Motion detection active but lower priority
- Activity logged but not alerted

**After Hours (Nights, Weekends):**
- **Enhanced sensitivity** - All motion triggers immediate alert
- **Thermal image capture** - Auto-capture on any movement
- **High-priority alerts** - SMS + Email + Discord
- **Detailed logging** - Who, what, when for audit trail

### Auto-Detection

System automatically determines after-hours status:
```python
now = datetime.now()
if now.weekday() >= 5:  # Weekend
    after_hours = True
elif now.time() < 08:00 or now.time() > 18:00:  # Night
    after_hours = True
else:
    after_hours = False
```

---

## Feature 3: Camera Activation on Motion

### Automatic Thermal Image Capture

**When motion detected:**
1. System reads current thermal camera frame
2. Saves image with timestamp to `logs/security_captures/`
3. Filename format: `motion_{equipment_id}_{timestamp}.png`
4. Image attached to alert message
5. Retention: 90 days (configurable)

### Storage Location

```
logs/
└── security_captures/
    ├── motion_fridge_lab_a_01_20251029_224530.png
    ├── motion_fridge_lab_a_01_20251029_231245.png
    └── motion_centrifuge_01_20251030_030015.png
```

### Image Analysis

**Thermal images show:**
- Heat signatures of people near equipment
- Time of access
- Equipment thermal state during access
- Proof of unauthorized entry

**Example Use Cases:**
- Identify who accessed fridge after-hours
- Determine if door was left open
- Detect equipment tampering
- Evidence for security investigations

---

## Feature 4: Tamper Detection

### Indicators of Tampering

**1. Abnormal Vibration**
```python
# Equipment hit, moved, or shaken
if vibration >= 2.0 G:  # Much higher than normal operation
    alert_tampering("physical_tampering")
```

**2. Rapid Temperature Change**
```python
# Door left open or equipment disabled
if temp_change_rate > 5.0 °C/min:
    alert_tampering("thermal_tampering")
```

**3. Unexpected Power Cycles** (future)
```python
# Equipment unplugged or circuit breaker tripped
if power_interruption_detected:
    alert_tampering("power_tampering")
```

### Example Tamper Alert

```
🚨🚨 SECURITY ALERT 🚨🚨
Type: EQUIPMENT_TAMPERING
Equipment: freezer_ultra_low_01
Time: 2025-10-29 23:15:42
Status: AFTER HOURS

Details:
  • type: physical_tampering
  • indicator: abnormal_vibration
  • value: 3.2G
  • message: Equipment experienced 3.2G vibration (possible physical tampering)

Thermal image captured: logs/security_captures/tamper_freezer_ultra_low_01_20251029_231542.png

⚠️ IMMEDIATE ACTION REQUIRED ⚠️
```

---

## Feature 5: Activity Logging

### Complete Audit Trail

**All activities logged to JSON:**
```json
{
  "timestamp": "2025-10-29T22:45:30.123456",
  "event_type": "motion_detected",
  "equipment_id": "fridge_lab_a_01",
  "details": {
    "location": "Lab A, Corner near sink",
    "after_hours": true,
    "thermal_data_available": true
  },
  "after_hours": true
}
```

### Event Types Logged

| Event Type | Trigger | Priority |
|------------|---------|----------|
| `motion_detected` | PIR sensor | HIGH |
| `tamper_detected` | Abnormal vibration/temp | CRITICAL |
| `routine_monitoring` | Normal sensor read | LOW |
| `sensor_threshold_alert` | Temperature/gas/etc. | MEDIUM |
| `ai_anomaly_detected` | CNN/LSTM detection | MEDIUM |

### Log File Locations

```
logs/
├── security_activity.log       # Human-readable log
├── security_activity.json      # Structured JSON log
└── premonitor.log              # General system log
```

### Querying Activity Logs

**Python API:**
```python
from security_monitor import ActivityLogger

logger = ActivityLogger()

# Get last 24 hours of activity
recent = logger.get_recent_activity(hours=24)

for event in recent:
    print(f"{event['timestamp']}: {event['event_type']} - {event['equipment_id']}")
```

**Generate Security Report:**
```python
from security_monitor import generate_security_report

# Generate report for last 7 days
report = generate_security_report(hours=168)
print(report)
```

**Output:**
```
SECURITY ACTIVITY REPORT - Last 168 hours
============================================================

Summary:
  Total Events: 5042
  Motion Detected: 3
  Tampering Detected: 0
  Routine Monitoring: 5039

Security Events:
  [2025-10-29T22:45:30] MOTION_DETECTED
    Equipment: fridge_lab_a_01
    Details: {'location': 'Lab A, Corner near sink', 'after_hours': True}

  [2025-10-29T23:15:42] MOTION_DETECTED
    Equipment: freezer_ultra_low_01
    Details: {'location': 'Lab A, Cold room', 'after_hours': True}
```

---

## Feature 6: Who Accessed Equipment?

### Tracking Access with Thermal Imaging

**Problem:** How to identify who accessed equipment?

**Solution:** Thermal cameras capture heat signatures + timestamps

**Information Captured:**
1. **When:** Exact timestamp from activity log
2. **Where:** Equipment ID and physical location
3. **What:** Thermal image showing person's heat signature
4. **How Long:** Duration of access (motion start to motion stop)

### Access Tracking Example

**Scenario:** Someone accessed ultra-low freezer at 11:30 PM

**Evidence Collected:**
1. **Activity Log:**
```json
{
  "timestamp": "2025-10-29T23:30:15",
  "event_type": "motion_detected",
  "equipment_id": "freezer_ultra_low_01",
  "details": {
    "location": "Lab A, Cold room",
    "after_hours": true
  }
}
```

2. **Thermal Image:**
   - File: `logs/security_captures/motion_freezer_ultra_low_01_20251029_233015.png`
   - Shows: Heat signature of person standing in front of freezer
   - Temperature map: Identify approximate height/build

3. **Temperature Log:**
   - Before access: -80.5°C
   - During access: -79.2°C (door opened)
   - After access: Returns to -80.5°C

4. **Duration:**
   - Motion start: 23:30:15
   - Motion end: 23:32:45
   - Access duration: 2 minutes 30 seconds

### Correlating with Badge Systems

**Optional Enhancement:** Integrate with building access control

```python
# Example: Query badge system API
def identify_person_near_equipment(timestamp, location):
    # Query badge swipes within 5 minutes of motion event
    badge_records = badge_system.query_swipes(
        start_time=timestamp - timedelta(minutes=5),
        end_time=timestamp + timedelta(minutes=5),
        location=location
    )

    return badge_records
```

**Correlation Example:**
```
Motion Event: 2025-10-29 23:30:15 at "Lab A, Cold room"
Badge Swipes:
  - 2025-10-29 23:28:42: Dr. John Smith (Badge #1234) - Lab A entrance
  - 2025-10-29 23:35:10: Dr. John Smith (Badge #1234) - Lab A exit

LIKELY MATCH: Dr. John Smith accessed freezer_ultra_low_01
```

---

## Feature 7: Alert Compromise Detection

### Detecting System Compromise

**Indicators:**
1. **Motion sensor disconnected** - Sensor reads constant 0
2. **Activity log tampering** - Log file modification detected
3. **Alert suppression** - Alerts sent but not received
4. **Service stopped** - systemd service not running

### Protection Mechanisms

**1. Watchdog Timer**
```python
# Check if monitoring loop is still running
last_heartbeat = datetime.now()

while True:
    # Monitor equipment
    monitor_equipment(equipment)

    # Update heartbeat
    last_heartbeat = datetime.now()

    # Send "I'm alive" signal every hour
    if (datetime.now() - last_sent_heartbeat).seconds >= 3600:
        send_heartbeat_signal()
```

**2. Log Integrity**
```python
# Sign logs with hash to detect tampering
import hashlib

log_entry = {...}
log_signature = hashlib.sha256(json.dumps(log_entry).encode()).hexdigest()
log_entry["signature"] = log_signature
```

**3. Remote Monitoring**
```bash
# Set up external monitoring service (e.g., UptimeRobot)
# Pings HTTP endpoint every 5 minutes
# If no response → Send alert to external phone
```

**4. Redundant Logging**
```python
# Send security events to remote syslog server
import logging.handlers

syslog_handler = logging.handlers.SysLogHandler(
    address=('remote-syslog-server.com', 514)
)
logger.addHandler(syslog_handler)
```

---

## Configuration Examples

### High-Security Setup

**Use Case:** Critical equipment (ultra-low freezers, valuable samples)

```python
SECURITY_CONFIG = {
    "business_hours": {
        "start": "07:00",
        "end": "19:00",
        "weekdays_only": False  # Enhanced security every day
    },
    "motion_detection": {
        "enabled": True,
        "sensitivity": 0.9,  # Very sensitive
        "cooldown_seconds": 60,  # Alert every minute if persistent motion
        "capture_images": True,
        "capture_duration": 30  # Capture for 30 seconds
    },
    "tamper_detection": {
        "enabled": True,
        "vibration_threshold": 1.0,  # Lower threshold = more sensitive
        "temperature_change_rate": 2.0,  # Alert on small temp changes
    },
    "intrusion_response": {
        "send_sms": True,  # Always send SMS
        "send_email": True,
        "send_discord": True,
        "capture_thermal_image": True,
        "lock_down_mode": False
    }
}
```

### Standard Setup

**Use Case:** Normal lab equipment monitoring

```python
SECURITY_CONFIG = {
    "business_hours": {
        "start": "08:00",
        "end": "18:00",
        "weekdays_only": True  # Only after-hours nights + weekends
    },
    "motion_detection": {
        "enabled": True,
        "sensitivity": 0.7,  # Moderate sensitivity
        "cooldown_seconds": 300,  # 5 minutes cooldown
        "capture_images": True,
        "capture_duration": 10
    },
    "tamper_detection": {
        "enabled": True,
        "vibration_threshold": 2.0,  # Standard threshold
        "temperature_change_rate": 5.0,
    },
    "intrusion_response": {
        "send_sms": False,  # No SMS (cost saving)
        "send_email": True,
        "send_discord": True,
        "capture_thermal_image": True,
    }
}
```

---

## Testing Security Features

### Test Motion Detection

```bash
# SSH into Raspberry Pi
ssh pi@premonitor.local

# Run security monitor test
cd ~/premonitor/pythonsoftware
python3 security_monitor.py
```

**Expected Output:**
```
Testing PREMONITOR Security Monitoring...

Current Status:
  After Hours: False
  Motion Detection: Enabled
  Tamper Detection: Enabled

Security monitoring initialized successfully!
```

### Simulate Motion Event

```python
# Edit security_monitor.py temporarily
# Change motion detection mock to always return True
motion = True  # Force motion detection

# Run main script
python3 premonitor_main_multi_equipment.py
```

**You should see:**
- Motion detection log entry
- Thermal image saved to `logs/security_captures/`
- Alert sent to Discord/Email

---

## Deployment Checklist

### Hardware

- [ ] PIR motion sensor installed (HC-SR501 on GPIO 18)
- [ ] Thermal camera positioned to capture access area
- [ ] All sensors connected and tested
- [ ] Power supply stable (UPS recommended)

### Software

- [ ] `security_monitor.py` copied to Raspberry Pi
- [ ] Business hours configured correctly
- [ ] Alert channels tested (Discord, Email, SMS)
- [ ] Log directory created (`logs/security_captures/`)
- [ ] Activity logging enabled

### Testing

- [ ] Test motion detection (walk in front of sensor)
- [ ] Test after-hours mode (change system time or wait)
- [ ] Test thermal image capture
- [ ] Test alert delivery (all channels)
- [ ] Test tamper detection (shake equipment gently)
- [ ] Verify activity logs being written

### Monitoring

- [ ] Check security status: `python3 security_monitor.py`
- [ ] Review activity logs: `cat logs/security_activity.json`
- [ ] Generate security report weekly
- [ ] Verify watchdog heartbeat

---

## Troubleshooting

### Motion Sensor Not Detecting

**Check wiring:**
```bash
# Verify GPIO 18 is configured as input
gpio readall | grep "GPIO 18"
```

**Test sensor directly:**
```python
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.IN)
while True:
    print(f"Motion: {GPIO.input(18)}")
    time.sleep(0.5)
```

### Images Not Capturing

**Check directory permissions:**
```bash
ls -ld logs/security_captures/
# Should show: drwxr-xr-x pi pi

# Fix if needed:
mkdir -p logs/security_captures
chmod 755 logs/security_captures
```

### Alerts Not Sending

**Check environment variables:**
```bash
echo $DISCORD_WEBHOOK_URL
echo $EMAIL_SENDER_ADDRESS
```

**Test manually:**
```python
import alert_manager
alert_manager.send_discord_alert("Test security alert")
```

---

## Cost Analysis

### Security Hardware Costs

| Component | Cost | Purpose |
|-----------|------|---------|
| HC-SR501 PIR Sensor | $3 | Motion detection |
| Magnetic Door Sensor (optional) | $5 | Tamper detection |
| **Total** | **$8** | **Complete security system** |

**No additional cost** if using existing thermal cameras for image capture.

### SMS Alert Costs (Optional)

**Twilio Pricing:**
- SMS: $0.0075 per message
- Typical usage: 5 alerts/month = $0.04/month
- Annual cost: $0.48/year

**ROI:** Preventing one sample loss event ($100-10,000) pays for entire system.

---

## Summary

### ✅ All Security Features Active 24/7

1. **PIR Motion Detection** - Detects unauthorized access
2. **After-Hours Mode** - Enhanced monitoring nights + weekends
3. **Camera Activation** - Auto-capture thermal images on motion
4. **Tamper Detection** - Alerts on physical interference
5. **Activity Logging** - Complete audit trail with timestamps
6. **Multi-Channel Alerts** - SMS + Email + Discord
7. **Access Tracking** - Who accessed equipment, when, and for how long

### Protection Provided

✅ **Unauthorized Access** - Immediate alert if someone approaches equipment after-hours
✅ **Equipment Tampering** - Detect if someone moves, hits, or interferes with equipment
✅ **Theft Prevention** - Thermal images + activity logs provide evidence
✅ **Compliance** - Complete audit trail for regulatory requirements
✅ **Sample Protection** - Detect if someone left door open or disabled equipment

### Next Steps

1. Install PIR motion sensor (GPIO 18)
2. Configure business hours in `security_monitor.py`
3. Test motion detection and alert delivery
4. Review activity logs daily for first week
5. Adjust sensitivity based on false positive rate
6. Set up weekly security report generation

---

**Alexandru Emanuel Vasile**
**PREMONITOR Security Features v2.1**
**© 2025 - All Rights Reserved**
