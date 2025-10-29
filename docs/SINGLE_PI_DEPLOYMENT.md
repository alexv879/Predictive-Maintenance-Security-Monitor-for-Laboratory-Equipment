# 🎯 Single Raspberry Pi Deployment Guide

## Overview

This guide covers deploying PREMONITOR to monitor **multiple equipment units from a SINGLE Raspberry Pi**. This is the most common and cost-effective setup for small to medium labs.

---

## ✅ What You Can Monitor (Single Pi)

A **single Raspberry Pi 4 (4GB RAM)** can monitor:
- **3-5 equipment units** simultaneously
- Each equipment can have multiple sensors
- Real-time AI inference on all equipment
- Independent alert routing per equipment

---

## 📋 Hardware Requirements

### Minimum (1 Equipment)
- 1× Raspberry Pi 4 (4GB RAM) - $75
- 1× MLX90640 Thermal Camera - $60
- 1× USB Microphone - $15
- 1× MicroSD Card (32GB) - $10
- 1× Power Supply (5V 3A) - $10
- **Total: ~$170**

### Recommended (3-5 Equipment)
- 1× Raspberry Pi 4 (4GB RAM) - $75
- 3-5× MLX90640 Thermal Cameras - $180-300
- 3-5× USB Microphones (or USB Audio Hub) - $45-75
- Optional: Gas sensors, temperature sensors - $20-50
- 1× MicroSD Card (64GB) - $15
- 1× Power Supply (5V 3A) - $10
- **Total: ~$345-525** ($115-175 per equipment)

---

## 🚀 Quick Start: Single Equipment (Fridge)

### Step 1: Hardware Setup

1. **Connect Thermal Camera (MLX90640):**
   ```
   Pi GPIO    → MLX90640
   Pin 1 (3.3V) → VCC
   Pin 6 (GND)  → GND
   Pin 3 (SDA)  → SDA
   Pin 5 (SCL)  → SCL
   ```

2. **Connect USB Microphone:**
   ```
   Plug into any USB port on Pi
   ```

3. **Connect Gas Sensor (Optional - MQ-2):**
   ```
   Pi GPIO     → MQ-2
   Pin 2 (5V)  → VCC
   Pin 6 (GND) → GND
   Pin 11 (GPIO17) → DOUT
   ```

4. **Connect Temperature Sensor (Optional - DS18B20):**
   ```
   Pi GPIO      → DS18B20
   Pin 1 (3.3V) → VCC (with 4.7kΩ pullup)
   Pin 6 (GND)  → GND
   Pin 7 (GPIO4) → DATA
   ```

### Step 2: Software Setup

**On your PC (Windows):**

```powershell
# 1. Train models (if not already done)
cd D:\PREMONITOR
python pythonsoftware\premonitor_train_models_py.py --model thermal
python pythonsoftware\premonitor_train_models_py.py --model acoustic
python pythonsoftware\premonitor_train_models_py.py --model lstm

# 2. Export to TFLite (creates .tflite files)
python pythonsoftware\export_tflite.py --model thermal --quantize int8
python pythonsoftware\export_tflite.py --model acoustic --quantize int8
python pythonsoftware\export_tflite.py --model lstm --quantize int8

# 3. Copy to Raspberry Pi
scp models\*.tflite pi@raspberrypi.local:/home/pi/premonitor/models/
scp pythonsoftware\*.py pi@raspberrypi.local:/home/pi/premonitor/
```

**On Raspberry Pi:**

```bash
# SSH into Pi
ssh pi@raspberrypi.local

# Create directory structure
mkdir -p ~/premonitor/models
mkdir -p ~/premonitor/logs

# Install dependencies
sudo apt-get update
sudo apt-get install -y python3-pip i2c-tools
pip3 install tflite-runtime numpy

# Enable I2C
sudo raspi-config
# Navigate to: Interface Options → I2C → Enable

# Reboot
sudo reboot
```

### Step 3: Configure Equipment

**On Raspberry Pi, edit `equipment_registry.py`:**

```bash
cd ~/premonitor
nano equipment_registry.py
```

**Current configuration (single fridge):**
```python
EQUIPMENT_REGISTRY = [
    {
        "id": "fridge_lab_a_01",
        "type": "fridge",
        "name": "Main Lab Fridge A1",
        "location": "Lab A, Corner near sink",
        "pi_id": "premonitor_pi",  # Single Pi for all equipment
        "sensors": {
            "thermal_camera": {"enabled": True, "i2c_address": "0x33"},
            "microphone": {"enabled": True, "device": "hw:1,0"},
            "gas_sensor": {"enabled": True, "gpio_pin": 17},
            "temperature": {"enabled": True, "gpio_pin": 4}
        },
        "alert_channels": ["discord", "email"],
        "critical": True
    }
]
```

**This is ready to use!** Just update:
- `name`: Your fridge's name
- `location`: Physical location
- `i2c_address`: Check with `i2cdetect -y 1`
- `device`: Check with `arecord -l`

### Step 4: Set Up Alerts

**Configure Discord webhook:**

```bash
nano alert_manager.py
```

Add your Discord webhook URL:
```python
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/YOUR_WEBHOOK_HERE"
```

**Configure email (optional):**

```bash
export EMAIL_SENDER_ADDRESS="your_email@gmail.com"
export EMAIL_SENDER_PASSWORD="your_app_password"
echo 'export EMAIL_SENDER_ADDRESS="your_email@gmail.com"' >> ~/.bashrc
echo 'export EMAIL_SENDER_PASSWORD="your_app_password"' >> ~/.bashrc
```

### Step 5: Test Configuration

```bash
cd ~/premonitor

# Validate equipment registry
python3 equipment_registry.py
```

**Expected output:**
```
✅ All equipment configurations valid!

Equipment by Pi:

premonitor_pi:
  - fridge_lab_a_01: Main Lab Fridge A1 🔴 CRITICAL
```

### Step 6: Run Monitoring

```bash
# Run in foreground (for testing)
python3 premonitor_main_multi_equipment.py
```

**Expected output:**
```
========================================================================
PREMONITOR Multi-Equipment Monitoring System - STARTUP
========================================================================
Starting monitoring for Pi: premonitor_pi
Monitoring 1 equipment units:
  - fridge_lab_a_01: Main Lab Fridge A1 (fridge)

--- Monitoring Cycle 1 ---
[fridge_lab_a_01] Reading sensors...
[fridge_lab_a_01] Thermal inference: 0.12 (Normal)
[fridge_lab_a_01] Acoustic inference: 0.08 (Normal)
```

**If working correctly, press Ctrl+C and set up as service (next step).**

### Step 7: Run as Background Service

```bash
# Create systemd service
sudo nano /etc/systemd/system/premonitor.service
```

**Add this content:**
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

**Enable and start:**
```bash
sudo systemctl enable premonitor
sudo systemctl start premonitor

# Check status
sudo systemctl status premonitor

# View logs
sudo journalctl -u premonitor -f
```

---

## 📈 Adding More Equipment (Same Pi)

### Example: Add a Second Fridge

**Edit `equipment_registry.py`:**

```python
EQUIPMENT_REGISTRY = [
    {
        "id": "fridge_lab_a_01",
        "type": "fridge",
        "name": "Main Lab Fridge A1",
        "location": "Lab A, Corner near sink",
        "pi_id": "premonitor_pi",
        "sensors": {
            "thermal_camera": {"enabled": True, "i2c_address": "0x33"},
            "microphone": {"enabled": True, "device": "hw:1,0"},
        },
        "alert_channels": ["discord"],
        "critical": True
    },
    {
        "id": "fridge_lab_a_02",  # NEW
        "type": "fridge",
        "name": "Secondary Lab Fridge A2",  # NEW
        "location": "Lab A, Near window",  # NEW
        "pi_id": "premonitor_pi",  # SAME PI
        "sensors": {
            "thermal_camera": {"enabled": True, "i2c_address": "0x34"},  # Different I2C
            "microphone": {"enabled": True, "device": "hw:2,0"},  # Different audio device
        },
        "alert_channels": ["discord"],
        "critical": False
    }
]
```

**Key changes:**
- Different `id` (unique identifier)
- Different `i2c_address` (0x33 → 0x34)
- Different `device` (hw:1,0 → hw:2,0)
- Same `pi_id` ("premonitor_pi")

**Restart service:**
```bash
sudo systemctl restart premonitor
sudo journalctl -u premonitor -f
```

**Output:**
```
Monitoring 2 equipment units:
  - fridge_lab_a_01: Main Lab Fridge A1 (fridge)
  - fridge_lab_a_02: Secondary Lab Fridge A2 (fridge)
```

---

## 🔧 Multi-Equipment Sensor Configuration

### Scenario: 3 Equipment on 1 Pi

**Equipment:**
1. Main Fridge (thermal + acoustic + gas)
2. Centrifuge (acoustic only)
3. Incubator (thermal + temperature)

**Hardware Connections:**

| Equipment | Sensor | Connection |
|-----------|--------|------------|
| **Fridge** | MLX90640 #1 | I2C address 0x33 |
| **Fridge** | USB Mic #1 | hw:1,0 |
| **Fridge** | MQ-2 Gas | GPIO17 |
| **Centrifuge** | USB Mic #2 | hw:2,0 |
| **Incubator** | MLX90640 #2 | I2C address 0x34 |
| **Incubator** | DS18B20 Temp | GPIO4 |

**Configuration:**

```python
EQUIPMENT_REGISTRY = [
    {
        "id": "fridge_01",
        "type": "fridge",
        "name": "Main Fridge",
        "pi_id": "premonitor_pi",
        "sensors": {
            "thermal_camera": {"enabled": True, "i2c_address": "0x33"},
            "microphone": {"enabled": True, "device": "hw:1,0"},
            "gas_sensor": {"enabled": True, "gpio_pin": 17}
        },
        "alert_channels": ["discord"],
        "critical": True
    },
    {
        "id": "centrifuge_01",
        "type": "centrifuge",
        "name": "Benchtop Centrifuge",
        "pi_id": "premonitor_pi",
        "sensors": {
            "microphone": {"enabled": True, "device": "hw:2,0"}
        },
        "alert_channels": ["discord"],
        "critical": False
    },
    {
        "id": "incubator_01",
        "type": "incubator",
        "name": "Cell Culture Incubator",
        "pi_id": "premonitor_pi",
        "sensors": {
            "thermal_camera": {"enabled": True, "i2c_address": "0x34"},
            "temperature": {"enabled": True, "gpio_pin": 4}
        },
        "alert_channels": ["discord"],
        "critical": True
    }
]
```

**Monitoring Cycle:**
```
Cycle 1 (30 seconds):
  - Monitor fridge_01 (thermal + acoustic + gas)
  - Monitor centrifuge_01 (acoustic)
  - Monitor incubator_01 (thermal + temperature)
  Total time: ~2-3 seconds per equipment = 6-9 seconds
  Sleep: 21-24 seconds

Cycle 2 (starts at 30 seconds):
  - Repeat...
```

---

## 💰 Cost Analysis: Single Pi Deployment

### 1 Equipment (MVP)
- **Hardware:** $170
- **Cost per equipment:** $170
- **Monthly cost:** $1-2 (electricity)

### 3 Equipment
- **Hardware:** $345-525
- **Cost per equipment:** $115-175
- **Savings vs 3 separate Pis:** ~$150-300

### 5 Equipment (Maximum for 1 Pi)
- **Hardware:** $520-750
- **Cost per equipment:** $104-150
- **Savings vs 5 separate Pis:** ~$300-500

**Economics:**
- **Single Pi:** $104-170 per equipment
- **Multiple Pis:** $135-215 per equipment
- **Savings:** ~$30-50 per equipment by consolidating on single Pi

---

## 📊 Performance Considerations

### Single Equipment
- **Inference time:** ~120 ms (thermal + acoustic + LSTM)
- **Sensor read time:** ~100 ms
- **Total cycle time:** ~220 ms
- **Monitoring interval:** 30 seconds
- **CPU usage:** ~20%
- **Memory usage:** ~500 MB

### Multiple Equipment (3 units)
- **Total cycle time:** ~660 ms (220 ms × 3)
- **Monitoring interval:** 30 seconds per equipment
- **CPU usage:** ~35%
- **Memory usage:** ~700 MB
- **Result:** Still plenty of headroom

### Maximum Capacity (5 units)
- **Total cycle time:** ~1,100 ms (220 ms × 5)
- **Monitoring interval:** 30 seconds (still achievable)
- **CPU usage:** ~50%
- **Memory usage:** ~900 MB
- **Result:** Near capacity but stable

**Recommendation:** Stick to **3-4 equipment units** per Pi for comfortable margins.

---

## 🆘 Troubleshooting

### No Equipment Detected
```bash
python3 equipment_registry.py
```
Check output - should show at least 1 equipment with `pi_id: premonitor_pi`

### I2C Device Not Found
```bash
sudo i2cdetect -y 1
```
Should show thermal camera at address 0x33 (or 0x34, etc.)

### Microphone Not Detected
```bash
arecord -l
```
Should show USB microphone as `card 1: Device` or similar

### Models Not Found
```bash
ls -lh ~/premonitor/models/
```
Should show:
- `thermal_anomaly_model.tflite` (~3 MB)
- `acoustic_anomaly_model.tflite` (~3 MB)
- `lstm_autoencoder_model.tflite` (~2 MB)

### High CPU Usage
Reduce monitoring frequency in `config.py`:
```python
SENSOR_READ_INTERVAL = 60  # Increase from 30 to 60 seconds
```

### Service Not Starting
```bash
sudo journalctl -u premonitor -n 50
```
Check logs for error messages

---

## 🎯 Next Steps

1. ✅ **Deploy MVP:** 1 Pi, 1 fridge (current setup)
2. ➡️ **Add Equipment:** Uncomment examples in `equipment_registry.py`
3. ➡️ **Fine-tune Thresholds:** Adjust per equipment type
4. ➡️ **Set Up Alerts:** Discord + Email
5. ➡️ **Monitor & Iterate:** Collect data, reduce false positives

---

## 📚 Related Documentation

- `equipment_registry.py` - Equipment configuration file
- `premonitor_main_multi_equipment.py` - Monitoring script
- `MULTI_EQUIPMENT_DEPLOYMENT.md` - Full deployment guide
- `SYSTEM_ARCHITECTURE_DIAGRAM.md` - System architecture

---

**🎉 You're monitoring multiple equipment from a single Raspberry Pi!**
