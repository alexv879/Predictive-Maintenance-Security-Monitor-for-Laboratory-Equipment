# 🚀 Multi-Equipment Deployment Guide

## Overview

The PREMONITOR system now supports monitoring **multiple lab equipment units** from a single or multiple Raspberry Pis. This guide covers deployment scenarios from a single-Pi setup to multi-site installations.

---

## 📋 Table of Contents

1. [Quick Start: Single Equipment](#quick-start-single-equipment)
2. [Multi-Equipment on Single Pi](#multi-equipment-on-single-pi)
3. [Multi-Pi Deployment](#multi-pi-deployment)
4. [Equipment Registry Configuration](#equipment-registry-configuration)
5. [Deployment Scenarios](#deployment-scenarios)
6. [Scaling & Economics](#scaling--economics)

---

## 🎯 Quick Start: Single Equipment

### Minimal Setup (1 Pi, 1 Fridge)

**Hardware Required:**
- 1x Raspberry Pi 4 (4GB RAM)
- 1x MLX90640 Thermal Camera
- 1x USB Microphone
- 1x MQ-2 Gas Sensor (optional)
- 1x DS18B20 Temperature Sensor (optional)

**Software Steps:**

```powershell
# 1. Copy trained models to Pi
scp models/*.tflite pi@raspberrypi:/home/pi/premonitor/models/

# 2. Copy Python scripts
scp pythonsoftware/*.py pi@raspberrypi:/home/pi/premonitor/

# 3. SSH into Pi and run
ssh pi@raspberrypi
cd /home/pi/premonitor
python3 premonitor_main_py.py
```

**Result:** Single fridge monitoring with thermal + acoustic AI models.

---

## 🏢 Multi-Equipment on Single Pi

### Scenario: 1 Pi Monitoring 3-5 Equipment Units

**Example Configuration:**
- **Pi ID:** `pi_refrigeration_01`
- **Equipment:**
  - Fridge A1 (thermal + acoustic + gas)
  - Fridge A2 (thermal + acoustic)
  - Ultra-Low Freezer (thermal + acoustic + temperature)

### Step 1: Edit Equipment Registry

Edit `pythonsoftware/equipment_registry.py`:

```python
EQUIPMENT_REGISTRY = [
    {
        "id": "fridge_lab_a_01",
        "type": "fridge",
        "name": "Main Lab Fridge A1",
        "location": "Lab A, Corner near sink",
        "pi_id": "pi_refrigeration_01",  # This Pi will monitor it
        "sensors": {
            "thermal_camera": {"enabled": True, "i2c_address": "0x33"},
            "microphone": {"enabled": True, "device": "hw:1,0"},
            "gas_sensor": {"enabled": True, "gpio_pin": 17}
        },
        "alert_channels": ["discord", "email"],
        "critical": True
    },
    {
        "id": "fridge_lab_a_02",
        "type": "fridge",
        "name": "Secondary Lab Fridge A2",
        "location": "Lab A, Near window",
        "pi_id": "pi_refrigeration_01",  # Same Pi
        "sensors": {
            "thermal_camera": {"enabled": True, "i2c_address": "0x34"},
            "microphone": {"enabled": True, "device": "hw:2,0"}
        },
        "alert_channels": ["discord"],
        "critical": False
    },
    {
        "id": "freezer_ultra_low_01",
        "type": "freezer_ultra_low",
        "name": "Ultra-Low Freezer -80°C",
        "location": "Lab A, Cold room",
        "pi_id": "pi_refrigeration_01",  # Same Pi
        "sensors": {
            "thermal_camera": {"enabled": True, "i2c_address": "0x35"},
            "microphone": {"enabled": True, "device": "hw:3,0"},
            "temperature": {"enabled": True, "gpio_pin": 4}
        },
        "alert_channels": ["discord", "email", "sms"],
        "critical": True
    }
]
```

### Step 2: Set Pi ID

On the Raspberry Pi, set the Pi ID:

```bash
# Option 1: Set hostname
sudo hostnamectl set-hostname pi_refrigeration_01

# Option 2: Set environment variable
echo 'export PREMONITOR_PI_ID="pi_refrigeration_01"' >> ~/.bashrc
source ~/.bashrc
```

### Step 3: Run Multi-Equipment Monitor

```bash
cd /home/pi/premonitor
python3 premonitor_main_multi_equipment.py
```

**Output:**
```
========================================================================
PREMONITOR Multi-Equipment Monitoring System - STARTUP
========================================================================
Starting monitoring for Pi: pi_refrigeration_01
Monitoring 3 equipment units:
  - fridge_lab_a_01: Main Lab Fridge A1 (fridge)
  - fridge_lab_a_02: Secondary Lab Fridge A2 (fridge)
  - freezer_ultra_low_01: Ultra-Low Freezer -80°C (freezer_ultra_low)

--- Monitoring Cycle 1 ---
[fridge_lab_a_01] Reading sensors...
[fridge_lab_a_01] Thermal inference: 0.12 (Normal)
[fridge_lab_a_01] Acoustic inference: 0.08 (Normal)
[fridge_lab_a_02] Reading sensors...
[fridge_lab_a_02] Thermal inference: 0.15 (Normal)
...
```

---

## 🌐 Multi-Pi Deployment

### Scenario: Multiple Pis, Multiple Equipment Types

**Network Architecture:**
```
┌─────────────────────────────────────────────────────┐
│                  LAB NETWORK                        │
│                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌────────┐   │
│  │ Pi #1        │  │ Pi #2        │  │ Pi #3  │   │
│  │ Refrigeration│  │ Incubation   │  │Mechanical│ │
│  └──────┬───────┘  └──────┬───────┘  └────┬───┘   │
│         │                 │                │       │
│    ┌────┴─────┐      ┌───┴────┐      ┌────┴────┐  │
│    │Fridge A1 │      │Incub #1│      │Centrifuge│ │
│    │Fridge A2 │      │Incub #2│      │Vac Pump │  │
│    │Freezer UL│      │         │      │         │  │
│    └──────────┘      └────────┘      └─────────┘  │
│                                                     │
│              All send alerts to:                   │
│         ┌─────────────────────────┐                │
│         │  Discord / Email / SMS  │                │
│         └─────────────────────────┘                │
└─────────────────────────────────────────────────────┘
```

### Configuration for 3 Pis

**Pi #1 - Refrigeration Equipment:**

```python
# On pi_refrigeration_01
EQUIPMENT_REGISTRY = [
    {"id": "fridge_lab_a_01", "pi_id": "pi_refrigeration_01", ...},
    {"id": "fridge_lab_a_02", "pi_id": "pi_refrigeration_01", ...},
    {"id": "freezer_ultra_low_01", "pi_id": "pi_refrigeration_01", ...}
]
```

**Pi #2 - Incubation Equipment:**

```python
# On pi_incubation_01
EQUIPMENT_REGISTRY = [
    {"id": "incubator_cell_01", "pi_id": "pi_incubation_01", ...},
    {"id": "incubator_cell_02", "pi_id": "pi_incubation_01", ...}
]
```

**Pi #3 - Mechanical Equipment:**

```python
# On pi_mechanical_01
EQUIPMENT_REGISTRY = [
    {"id": "centrifuge_01", "pi_id": "pi_mechanical_01", ...},
    {"id": "vacuum_pump_01", "pi_id": "pi_mechanical_01", ...},
    {"id": "shaker_01", "pi_id": "pi_mechanical_01", ...}
]
```

### Deployment Commands

```bash
# Deploy to Pi #1
scp models/*.tflite pi@pi-refrigeration:/home/pi/premonitor/models/
scp pythonsoftware/*.py pi@pi-refrigeration:/home/pi/premonitor/
ssh pi@pi-refrigeration "cd premonitor && python3 premonitor_main_multi_equipment.py &"

# Deploy to Pi #2
scp models/*.tflite pi@pi-incubation:/home/pi/premonitor/models/
scp pythonsoftware/*.py pi@pi-incubation:/home/pi/premonitor/
ssh pi@pi-incubation "cd premonitor && python3 premonitor_main_multi_equipment.py &"

# Deploy to Pi #3
scp models/*.tflite pi@pi-mechanical:/home/pi/premonitor/models/
scp pythonsoftware/*.py pi@pi-mechanical:/home/pi/premonitor/
ssh pi@pi-mechanical "cd premonitor && python3 premonitor_main_multi_equipment.py &"
```

---

## 📝 Equipment Registry Configuration

### Adding New Equipment

**Example: Add a Centrifuge**

1. Open `pythonsoftware/equipment_registry.py`
2. Add equipment entry to `EQUIPMENT_REGISTRY`:

```python
{
    "id": "centrifuge_02",  # Unique ID
    "type": "centrifuge",   # Equipment type (must exist in EQUIPMENT_TYPES)
    "name": "Benchtop Centrifuge #2",  # Human-readable name
    "location": "Lab B, Bench 5",      # Physical location
    "pi_id": "pi_mechanical_01",       # Which Pi monitors this
    "sensors": {
        "microphone": {
            "enabled": True,
            "device": "hw:3,0",
            "sample_rate": 16000,
            "channels": 1
        },
        "vibration": {
            "enabled": True,
            "i2c_address": "0x55",
            "sensor_type": "ADXL345",
            "range": "±16g"
        }
    },
    "alert_channels": ["discord", "email"],  # Where to send alerts
    "maintenance_schedule": "Semi-annually",
    "critical": False,  # True = more urgent alerts
    "notes": "New centrifuge - monitor bearing wear"
}
```

3. Restart the Pi:

```bash
ssh pi@pi-mechanical
pkill -f premonitor_main_multi_equipment.py
python3 premonitor_main_multi_equipment.py &
```

### Equipment Types Available

| Type | Required Sensors | Models Used |
|------|-----------------|-------------|
| `fridge` | thermal, acoustic | thermal_cnn, acoustic_cnn, lstm_ae |
| `freezer_ultra_low` | thermal, acoustic, temperature | thermal_cnn, acoustic_cnn, lstm_ae |
| `incubator` | thermal, temperature | thermal_cnn, lstm_ae |
| `centrifuge` | acoustic | acoustic_cnn, lstm_ae |
| `autoclave` | thermal, acoustic | thermal_cnn, acoustic_cnn, lstm_ae |
| `oven` | thermal | thermal_cnn, lstm_ae |
| `water_bath` | thermal, temperature | thermal_cnn, lstm_ae |
| `vacuum_pump` | acoustic | acoustic_cnn, lstm_ae |
| `fume_hood` | acoustic | acoustic_cnn |
| `shaker` | acoustic | acoustic_cnn |

### Equipment-Specific Thresholds

Thresholds are automatically loaded from `EQUIPMENT_THRESHOLDS` in `equipment_registry.py`:

```python
EQUIPMENT_THRESHOLDS = {
    "centrifuge": {
        "acoustic_anomaly_confidence": 0.75,  # Very sensitive (safety critical)
        "lstm_reconstruction_threshold": 0.050,
        "vibration_threshold": 0.5,  # G-force
        "current_threshold": 5.0  # Amps
    },
    "freezer_ultra_low": {
        "thermal_anomaly_confidence": 0.85,
        "acoustic_anomaly_confidence": 0.80,  # More sensitive (expensive samples)
        "temperature_range": (-82.0, -78.0)
    }
}
```

To customize thresholds, edit the corresponding entry in `equipment_registry.py`.

---

## 🎬 Deployment Scenarios

### Scenario 1: Small Lab (5-10 Equipment)

**Recommended:** 2-3 Raspberry Pis

```
Pi #1: All refrigeration (fridges + freezers)
Pi #2: All mechanical (centrifuges, pumps, shakers)
Pi #3: All heating (incubators, ovens, autoclaves)
```

**Cost:** $150-300 (3x Pi @ $50-100 each)
**Sensors:** ~$300-600 total
**Total:** ~$450-900

### Scenario 2: Medium Lab (10-20 Equipment)

**Recommended:** 4-5 Raspberry Pis

```
Pi #1: Refrigeration (fridges, freezers)
Pi #2: Incubation (incubators, water baths)
Pi #3: Mechanical (centrifuges, pumps)
Pi #4: Safety (fume hoods, autoclaves)
Pi #5: Backup/Testing
```

**Cost:** $250-500 (5x Pi)
**Sensors:** ~$600-1,200
**Total:** ~$850-1,700

### Scenario 3: Multi-Site Enterprise

**Recommended:** 1-2 Pis per site, centralized alerting

```
Site A (Main Lab): 5 Pis
Site B (Research Lab): 3 Pis
Site C (Production): 4 Pis

All send alerts to:
- Centralized Discord server
- Email distribution list
- SMS for critical equipment
```

**Cost:** 12 Pis × $75 = $900
**Sensors:** ~$2,400
**Total:** ~$3,300 for 30-50 equipment units

---

## 💰 Scaling & Economics

### Cost per Equipment Unit

| Component | Cost | Notes |
|-----------|------|-------|
| Thermal Camera (MLX90640) | $50-80 | Required for thermal monitoring |
| USB Microphone | $10-20 | Required for acoustic monitoring |
| Gas Sensor (MQ-2/MQ-135) | $5-10 | Optional |
| Temperature Sensor (DS18B20) | $2-5 | Optional |
| Vibration Sensor (ADXL345) | $5-15 | Optional (mechanical equipment) |
| Current Sensor (INA219) | $5-10 | Optional (motor equipment) |
| **Per-Equipment Total** | **$60-140** | Varies by sensor requirements |

### Raspberry Pi Allocation

- **1 Pi** can monitor **3-5 equipment units** (depending on sensor density)
- **Pi Cost:** $50-100 (Pi 4, 4GB RAM)
- **Per-Equipment Pi Cost (amortized):** $10-33

### Total System Cost Examples

| Equipment Count | Pis Needed | Pi Cost | Sensor Cost | Total | $/Equipment |
|----------------|-----------|---------|-------------|-------|-------------|
| 1 (MVP) | 1 | $75 | $60-140 | $135-215 | $135-215 |
| 5 | 2 | $150 | $300-700 | $450-850 | $90-170 |
| 10 | 3 | $225 | $600-1,400 | $825-1,625 | $83-163 |
| 20 | 5 | $375 | $1,200-2,800 | $1,575-3,175 | $79-159 |
| 50 | 12 | $900 | $3,000-7,000 | $3,900-7,900 | $78-158 |

**Economies of Scale:** Cost per equipment drops from ~$200 (single unit) to ~$80-160 (bulk deployment).

---

## 🔧 Configuration Management

### Centralized vs. Distributed Configuration

**Option 1: Single Registry File (Centralized)**
- One `equipment_registry.py` file with ALL equipment
- Each Pi filters by `pi_id` to get its assigned equipment
- **Pros:** Single source of truth, easy updates
- **Cons:** Must redeploy to all Pis on changes

**Option 2: Pi-Specific Config Files (Distributed)**
- Each Pi has its own `equipment_registry.py`
- Only contains equipment for that Pi
- **Pros:** Isolated deployments, no unnecessary data
- **Cons:** Harder to maintain consistency

**Recommended:** Start with Option 1 (centralized), switch to Option 2 for large deployments (20+ Pis).

---

## 🚀 Quick Commands

### Validate Equipment Registry

```bash
python3 equipment_registry.py
```

Output:
```
================================================================================
                     EQUIPMENT REGISTRY VALIDATION
================================================================================

Total equipment registered: 6
Equipment types available: 10
Raspberry Pis in use: 3

✅ All equipment configurations valid!

Equipment by Pi:

pi_refrigeration_01:
  - fridge_lab_a_01: Main Lab Fridge A1 🔴 CRITICAL
  - freezer_ultra_low_01: Ultra-Low Freezer -80°C 🔴 CRITICAL

pi_incubation_01:
  - incubator_cell_01: Cell Culture Incubator #1 🔴 CRITICAL

pi_mechanical_01:
  - centrifuge_01: Benchtop Centrifuge #1
  - vacuum_pump_01: Rotary Vane Vacuum Pump
```

### Start Multi-Equipment Monitoring

```bash
# On each Pi
python3 premonitor_main_multi_equipment.py
```

### Run as Background Service

```bash
# Create systemd service
sudo nano /etc/systemd/system/premonitor.service
```

```ini
[Unit]
Description=PREMONITOR Multi-Equipment Monitoring
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/premonitor
ExecStart=/usr/bin/python3 /home/pi/premonitor/premonitor_main_multi_equipment.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl enable premonitor
sudo systemctl start premonitor

# Check status
sudo systemctl status premonitor

# View logs
sudo journalctl -u premonitor -f
```

---

## 📊 Monitoring Dashboard (Future)

### Centralized Web Dashboard

**Planned Features:**
- Real-time equipment status (all sites)
- Historical anomaly trends
- Alert history and acknowledgment
- Equipment health scores
- Maintenance scheduling

**Tech Stack:**
- Flask/FastAPI backend
- React/Vue.js frontend
- PostgreSQL database
- WebSocket for real-time updates

**Deployment:** Cloud server or local lab server

---

## 🆘 Troubleshooting

### Equipment Not Detected

```bash
# Check Pi ID
echo $PREMONITOR_PI_ID
hostname

# Validate registry
python3 equipment_registry.py

# Check sensor connections
i2cdetect -y 1  # Thermal cameras
arecord -l      # Microphones
```

### Alerts Not Sending

```bash
# Check Discord webhook
curl -X POST <YOUR_WEBHOOK_URL> -d '{"content": "Test"}'

# Check email credentials
echo $EMAIL_SENDER_ADDRESS
echo $EMAIL_SENDER_PASSWORD

# Check alert_manager logs
python3 -c "import alert_manager; alert_manager.send_discord_alert('Test')"
```

### High CPU Usage

```bash
# Check running processes
htop

# Reduce monitoring frequency
# Edit config.py:
SENSOR_READ_INTERVAL = 60  # Increase from 30 to 60 seconds

# Disable LSTM for some equipment
# Edit equipment_registry.py and remove lstm_ae from models list
```

---

## 🎯 Next Steps

1. **Deploy MVP:** Start with 1 Pi, 1 fridge
2. **Add Equipment:** Add 2-3 more equipment units to same Pi
3. **Scale Horizontally:** Add second Pi for different equipment category
4. **Centralize Alerting:** Set up unified Discord channel for all Pis
5. **Build Dashboard:** Create web dashboard for centralized monitoring

---

## 📚 Related Documentation

- [Dataset Integration Guide](./DATASET_INVENTORY.md)
- [Training & Deployment Guide](./TRAINING_DEPLOYMENT_GUIDE.md)
- [Equipment Expansion Strategy](./MULTI_EQUIPMENT_EXPANSION.md)
- [Quick Reference](./QUICK_REFERENCE.md)

---

**🎉 You're now ready to deploy PREMONITOR across your entire lab!**
