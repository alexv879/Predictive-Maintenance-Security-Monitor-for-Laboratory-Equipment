# 🎯 Single Raspberry Pi Architecture

## System Overview: All Equipment → One Pi

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SINGLE RASPBERRY PI SETUP                        │
│                    (pi_id: "premonitor_pi")                         │
└─────────────────────────────────────────────────────────────────────┘

                    ┌───────────────────────┐
                    │   Raspberry Pi 4      │
                    │   (4GB RAM)           │
                    │                       │
                    │  • 3 AI Models        │
                    │    (8 MB total)       │
                    │  • ~500-900 MB RAM    │
                    │  • ~20-50% CPU        │
                    └───────┬───────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  EQUIPMENT 1  │   │  EQUIPMENT 2  │   │  EQUIPMENT 3  │
│               │   │               │   │               │
│  Main Fridge  │   │  Centrifuge   │   │  Incubator    │
│               │   │               │   │               │
│  Sensors:     │   │  Sensors:     │   │  Sensors:     │
│  • Thermal    │   │  • Acoustic   │   │  • Thermal    │
│  • Acoustic   │   │  • Vibration  │   │  • Temp       │
│  • Gas        │   │               │   │               │
│  • Temp       │   │               │   │               │
│               │   │               │   │               │
│  I2C: 0x33    │   │  Audio: hw:2,0│   │  I2C: 0x34    │
│  Audio: hw:1,0│   │               │   │  GPIO: 4      │
│  GPIO: 17     │   │               │   │               │
└───────────────┘   └───────────────┘   └───────────────┘
```

---

## Monitoring Flow (Single Pi, Multiple Equipment)

```
┌────────────────────────────────────────────────────────────┐
│              START MONITORING LOOP                         │
│              Pi ID: "premonitor_pi"                        │
└────────────────────────────────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────────┐
│  Load Equipment Registry                                   │
│  Filter by pi_id = "premonitor_pi"                        │
│  Result: All equipment (fridge, centrifuge, incubator)    │
└────────────────────────────────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────────┐
│  EQUIPMENT 1: fridge_01                                    │
│  ├─ Read sensors (thermal, acoustic, gas, temp)           │
│  ├─ Thermal CNN inference → 0.12 (Normal)                 │
│  ├─ Acoustic CNN inference → 0.08 (Normal)                │
│  ├─ LSTM-AE inference → 0.032 (Normal)                    │
│  └─ Check thresholds (0.85) → No anomaly                  │
│  Time: ~220 ms                                             │
└────────────────────────────────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────────┐
│  EQUIPMENT 2: centrifuge_01                                │
│  ├─ Read sensors (acoustic, vibration)                    │
│  ├─ Acoustic CNN inference → 0.09 (Normal)                │
│  ├─ LSTM-AE inference → 0.035 (Normal)                    │
│  └─ Check thresholds (0.75) → No anomaly                  │
│  Time: ~180 ms                                             │
└────────────────────────────────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────────┐
│  EQUIPMENT 3: incubator_01                                 │
│  ├─ Read sensors (thermal, temperature)                   │
│  ├─ Thermal CNN inference → 0.15 (Normal)                 │
│  ├─ LSTM-AE inference → 0.028 (Normal)                    │
│  └─ Check thresholds (0.90) → No anomaly                  │
│  Time: ~200 ms                                             │
└────────────────────────────────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────────┐
│  Total cycle time: ~600 ms                                 │
│  Sleep: 29.4 seconds                                       │
│  Next cycle starts at: 30 seconds                          │
└────────────────────────────────────────────────────────────┘
                         ↓
                   [REPEAT LOOP]
```

---

## Hardware Connections (Single Pi)

```
┌─────────────────────────────────────────────────────────────────┐
│                    RASPBERRY PI 4                               │
│                                                                 │
│  GPIO Header                                                    │
│  ┌────────┐                                                     │
│  │ Pin 1  │──────────→ MLX90640 #1 (Fridge) VCC (3.3V)        │
│  │ Pin 3  │──────────→ MLX90640 #1 SDA (I2C Address: 0x33)    │
│  │ Pin 5  │──────────→ MLX90640 #1 SCL                         │
│  │ Pin 6  │──────────→ MLX90640 #1 GND                         │
│  │        │                                                     │
│  │ Pin 1  │──────────→ MLX90640 #2 (Incubator) VCC            │
│  │ Pin 3  │──────────→ MLX90640 #2 SDA (I2C Address: 0x34)    │
│  │ Pin 5  │──────────→ MLX90640 #2 SCL                         │
│  │ Pin 6  │──────────→ MLX90640 #2 GND                         │
│  │        │                                                     │
│  │ Pin 7  │──────────→ DS18B20 (Temp Sensor) DATA (GPIO4)     │
│  │ Pin 11 │──────────→ MQ-2 (Gas Sensor) DOUT (GPIO17)        │
│  └────────┘                                                     │
│                                                                 │
│  USB Ports                                                      │
│  ┌────────┐                                                     │
│  │ USB 1  │──────────→ Microphone #1 (Fridge) hw:1,0          │
│  │ USB 2  │──────────→ Microphone #2 (Centrifuge) hw:2,0      │
│  │ USB 3  │──────────→ [Available for expansion]              │
│  │ USB 4  │──────────→ [Available for expansion]              │
│  └────────┘                                                     │
│                                                                 │
│  Network                                                        │
│  ┌────────┐                                                     │
│  │ Ethernet│─────────→ Local network (for alerts)             │
│  └────────┘                                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Equipment Registry Configuration (Single Pi)

```python
EQUIPMENT_REGISTRY = [
    # All equipment has SAME pi_id: "premonitor_pi"
    
    {
        "id": "fridge_01",           # Unique ID
        "type": "fridge",
        "pi_id": "premonitor_pi",    # ← SAME PI
        "sensors": {
            "thermal_camera": {"i2c_address": "0x33"},  # Different address
            "microphone": {"device": "hw:1,0"}          # Different device
        }
    },
    
    {
        "id": "centrifuge_01",       # Unique ID
        "type": "centrifuge",
        "pi_id": "premonitor_pi",    # ← SAME PI
        "sensors": {
            "microphone": {"device": "hw:2,0"}          # Different device
        }
    },
    
    {
        "id": "incubator_01",        # Unique ID
        "type": "incubator",
        "pi_id": "premonitor_pi",    # ← SAME PI
        "sensors": {
            "thermal_camera": {"i2c_address": "0x34"},  # Different address
            "temperature": {"gpio_pin": 4}
        }
    }
]
```

**Key Points:**
- ✅ All equipment: `pi_id = "premonitor_pi"`
- ✅ Different I2C addresses (0x33, 0x34, 0x35, etc.)
- ✅ Different audio devices (hw:1,0, hw:2,0, hw:3,0, etc.)
- ✅ Different GPIO pins (4, 5, 6, etc.)

---

## Scaling on Single Pi

### Current Setup (1 Equipment)
```
Pi Load:
├─ CPU: ~20%
├─ RAM: ~500 MB
├─ Sensors: 4 (thermal, acoustic, gas, temp)
├─ AI Models: 3 (thermal, acoustic, LSTM)
└─ Status: Plenty of headroom ✅
```

### Recommended (3 Equipment)
```
Pi Load:
├─ CPU: ~35%
├─ RAM: ~700 MB
├─ Total sensors: 9-12
├─ AI Models: 3 (shared across all equipment)
└─ Status: Comfortable margins ✅
```

### Maximum (5 Equipment)
```
Pi Load:
├─ CPU: ~50%
├─ RAM: ~900 MB
├─ Total sensors: 15-20
├─ AI Models: 3 (shared across all equipment)
└─ Status: Near capacity, stable ⚠️
```

**Recommendation:** 3-4 equipment per Pi for best performance.

---

## Alert Flow (All Equipment → Same Channels)

```
┌────────────────────────────────────────────────────────────┐
│  ANOMALY DETECTED                                          │
│  Equipment: fridge_01 (Main Fridge)                       │
│  Type: Thermal anomaly                                     │
│  Confidence: 0.89 (threshold: 0.85)                       │
└────────────────────┬───────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
┌──────────┐  ┌──────────┐  ┌──────────┐
│ Discord  │  │  Email   │  │   SMS    │
│          │  │          │  │          │
│ Webhook  │  │  SMTP    │  │ Twilio   │
└──────────┘  └──────────┘  └──────────┘

Alert Message:
🚨 ANOMALY DETECTED: Main Fridge (fridge_01)
Location: Lab A, Corner near sink
Equipment Type: fridge

• Thermal anomaly detected (confidence: 0.89)

Timestamp: 2025-10-29 14:32:15
```

---

## Cost Comparison: Single Pi vs Multiple Pis

### Scenario: 3 Equipment Units

**Option 1: Single Pi (Recommended)**
```
1× Raspberry Pi 4 (4GB)     $75
3× MLX90640 Thermal         $180
3× USB Microphones          $45
3× Gas Sensors              $30
1× Power Supply             $10
1× MicroSD Card             $15
────────────────────────
Total:                      $355
Cost per equipment:         $118
```

**Option 2: Three Separate Pis**
```
3× Raspberry Pi 4 (4GB)     $225
3× MLX90640 Thermal         $180
3× USB Microphones          $45
3× Gas Sensors              $30
3× Power Supplies           $30
3× MicroSD Cards            $45
────────────────────────
Total:                      $555
Cost per equipment:         $185
```

**Savings with Single Pi: $200 (~36%)**

---

## Performance Comparison

| Metric | Single Pi (3 Equipment) | Multiple Pis (3 Equipment) |
|--------|------------------------|---------------------------|
| **Hardware Cost** | $355 | $555 |
| **Power Consumption** | ~3W | ~9W |
| **Monthly Electricity** | ~$0.65 | ~$1.95 |
| **Maintenance** | 1 device | 3 devices |
| **Network Ports** | 1 | 3 |
| **Physical Space** | Minimal | 3× |
| **Deployment Time** | 15 min | 45 min |
| **Reliability** | Single point of failure | Redundant |

**Best For:**
- **Single Pi:** Small labs, cost-sensitive, 1-5 equipment in close proximity
- **Multiple Pis:** Large labs, critical redundancy, equipment spread across building

---

## 🎯 Quick Commands

### Validate Configuration
```bash
python3 equipment_registry.py
```

### Check Sensors
```bash
# I2C devices (thermal cameras)
sudo i2cdetect -y 1

# Audio devices (microphones)
arecord -l

# Temperature sensors
ls -l /sys/bus/w1/devices/
```

### Start Monitoring
```bash
# Foreground (testing)
python3 premonitor_main_multi_equipment.py

# Background (production)
sudo systemctl start premonitor
sudo journalctl -u premonitor -f
```

### Add Equipment
```bash
# Edit registry
nano equipment_registry.py

# Add new equipment block with:
# - Unique "id"
# - Same "pi_id": "premonitor_pi"
# - Different sensor addresses/pins

# Restart
sudo systemctl restart premonitor
```

---

**🎉 Single Pi, Multiple Equipment - Simple and Cost-Effective!**
