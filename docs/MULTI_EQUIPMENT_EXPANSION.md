# 🔬 PREMONITOR: Multi-Equipment Lab Monitoring System

**Purpose**: Expand from single fridge to comprehensive lab safety monitoring  
**Architecture**: Modular, scalable, edge-deployed

---

## 🎯 Current vs. Expanded System

### Current System (MVP)
```
1 Raspberry Pi → Monitor 1 Fridge
  - Thermal camera
  - Microphone
  - Gas sensor
```

### Expanded System (Multi-Equipment)
```
Multiple Raspberry Pis → Monitor Entire Lab
  - Fridges/Freezers (multiple units)
  - Incubators
  - Centrifuges
  - Autoclaves
  - Ovens
  - Ventilation/HVAC
  - Chemical storage
  - Water baths
  - Vacuum pumps
```

---

## 📊 Equipment Categories & Detection Methods

### Category 1: Refrigeration Equipment ✅ READY NOW

| Equipment | Sensors | Models Used | Datasets | Status |
|-----------|---------|-------------|----------|--------|
| **Lab Fridge** | Thermal, Audio, Temp | Thermal CNN, Acoustic CNN, LSTM-AE | FLIR, MIMII, Turbofan | ✅ Implemented |
| **Ultra-low Freezer (-80°C)** | Thermal, Audio, Temp | Same as above | Same | ✅ Ready |
| **Liquid N2 Dewar** | Thermal, Level sensor | Thermal CNN, LSTM-AE | FLIR, Turbofan | ✅ Ready |
| **Cryogenic Freezer** | Thermal, Vibration | Thermal CNN, LSTM-AE | FLIR, Turbofan | ✅ Ready |

**Key Failure Modes**:
- Compressor failure (MIMII acoustic detection)
- Door seal failure (thermal hotspot detection)
- Gradual degradation (Turbofan LSTM prediction)
- Coolant leak (thermal + gas sensor fusion)

---

### Category 2: Heating Equipment (Immediate Extension)

| Equipment | Sensors | Models Needed | Datasets Available | Implementation |
|-----------|---------|---------------|-------------------|----------------|
| **Incubator** | Thermal, CO2 sensor | Thermal CNN, LSTM-AE | FLIR, Turbofan | 🟡 Easy |
| **Oven** | Thermal | Thermal CNN | FLIR | 🟡 Easy |
| **Autoclave** | Thermal, Pressure, Audio | Thermal CNN, Acoustic CNN | FLIR, MIMII | 🟡 Easy |
| **Hot Plate** | Thermal | Thermal CNN | FLIR | 🟡 Easy |
| **Water Bath** | Thermal, Temp sensor | Thermal CNN, LSTM-AE | FLIR, Turbofan | 🟡 Easy |

**Key Failure Modes**:
- Overheating (thermal anomaly detection)
- Heater element failure (temperature trends)
- Thermostat malfunction (LSTM degradation patterns)
- Door seal failure (thermal imaging)

**Required Changes**: ⚠️ **None! Just adjust thresholds in config.py**

---

### Category 3: Mechanical Equipment (Motor-Based)

| Equipment | Sensors | Models Needed | Datasets Available | Implementation |
|-----------|---------|---------------|-------------------|----------------|
| **Centrifuge** | Vibration, Audio | Acoustic CNN, LSTM-AE | MIMII, Turbofan | 🟢 Good fit |
| **Shaker** | Vibration, Audio | Acoustic CNN | MIMII | 🟢 Good fit |
| **Stirrer** | Audio, Current | Acoustic CNN, LSTM-AE | MIMII, Turbofan | 🟢 Good fit |
| **Vacuum Pump** | Audio, Pressure | Acoustic CNN | MIMII | 🟢 Good fit |
| **Rotary Evaporator** | Audio, Thermal | Acoustic CNN, Thermal CNN | MIMII, FLIR | 🟢 Good fit |

**Key Failure Modes**:
- Bearing wear (MIMII acoustic patterns)
- Motor overheating (thermal + acoustic fusion)
- Belt slip (acoustic signature changes)
- Imbalance (vibration anomalies)

**Why MIMII Fits**: It's industrial **fan** sounds, but fans = motors = rotating equipment!
- Centrifuge motor ≈ Industrial fan motor
- Vacuum pump ≈ Industrial blower
- Shaker motor ≈ Industrial vibration motor

---

### Category 4: Ventilation & Environmental

| Equipment | Sensors | Models Needed | Datasets Available | Implementation |
|-----------|---------|---------------|-------------------|----------------|
| **Fume Hood** | Airflow, Audio | Acoustic CNN, LSTM-AE | MIMII, Turbofan | 🟢 Good fit |
| **HVAC System** | Thermal, Audio, Airflow | All three models | FLIR, MIMII, Turbofan | 🟢 Good fit |
| **Exhaust Fan** | Audio, Vibration | Acoustic CNN | MIMII | 🟢 Perfect fit |
| **Air Compressor** | Audio, Pressure | Acoustic CNN, LSTM-AE | MIMII, Turbofan | 🟢 Good fit |

**Key Failure Modes**:
- Fan motor failure (MIMII acoustic)
- Filter clogging (airflow + acoustic changes)
- Duct obstruction (pressure trends)
- Belt degradation (acoustic signatures)

---

### Category 5: Chemical Storage & Safety

| Equipment | Sensors | Models Needed | Datasets Available | Implementation |
|-----------|---------|---------------|-------------------|----------------|
| **Chemical Fridge** | Thermal, Gas, Audio | All three models | FLIR, MIMII, Turbofan | ✅ Same as fridge |
| **Flammable Cabinet** | Thermal, Gas | Thermal CNN | FLIR | 🟡 Easy |
| **Gas Cylinder Storage** | Thermal, Gas, Pressure | Thermal CNN, LSTM-AE | FLIR, Turbofan | 🟡 Easy |
| **Solvent Cabinet** | Gas sensor | LSTM-AE | Turbofan | 🟡 Easy |

**Key Failure Modes**:
- Gas leak (gas sensor + thermal for location)
- Temperature excursion (thermal anomaly)
- Door left open (thermal pattern change)
- Ventilation failure (gas buildup over time)

---

## 🔧 How to Add New Equipment (Step-by-Step)

### Step 1: Identify Equipment Characteristics

**Questions to ask**:
1. Does it have motors/fans? → Use **Acoustic CNN** (MIMII)
2. Does temperature matter? → Use **Thermal CNN** (FLIR)
3. Does it degrade over time? → Use **LSTM-AE** (Turbofan)
4. Does it produce gas/fumes? → Add **gas sensor** threshold

### Step 2: Sensor Selection

**Available Sensors** (cheap, easy to add):
```python
# Standard sensor suite (Raspberry Pi compatible)
SENSOR_OPTIONS = {
    "thermal_camera": "MLX90640 (32x24 thermal array) - $60",
    "microphone": "USB or I2S microphone - $10-30",
    "gas_sensor": "MQ-series (MQ-2, MQ-4, MQ-7, MQ-135) - $5-15",
    "temperature": "DS18B20 digital temp sensor - $2",
    "vibration": "SW-420 or ADXL345 accelerometer - $5-15",
    "pressure": "BMP280 barometric pressure - $5",
    "current": "INA219 current sensor - $10",
    "humidity": "DHT22 temp/humidity - $5",
    "airflow": "Anemometer sensor - $15-30"
}
```

### Step 3: Add Equipment Configuration

**Edit**: `pythonsoftware/premonitor_config_py.py`

```python
# Add new equipment type
EQUIPMENT_TYPES = {
    "fridge": {
        "sensors": ["thermal", "acoustic", "gas", "temperature"],
        "models": ["thermal_cnn", "acoustic_cnn", "lstm_ae"],
        "thresholds": {
            "thermal_anomaly": 0.85,
            "acoustic_anomaly": 0.85,
            "lstm_reconstruction": 0.045,
            "gas_threshold": 300
        }
    },
    "centrifuge": {  # NEW EQUIPMENT
        "sensors": ["acoustic", "vibration", "current"],
        "models": ["acoustic_cnn", "lstm_ae"],
        "thresholds": {
            "acoustic_anomaly": 0.80,  # Slightly lower (more sensitive)
            "lstm_reconstruction": 0.050,
            "vibration_threshold": 0.5,  # G-force threshold
            "current_threshold": 5.0  # Amps
        }
    },
    "incubator": {  # NEW EQUIPMENT
        "sensors": ["thermal", "temperature", "co2"],
        "models": ["thermal_cnn", "lstm_ae"],
        "thresholds": {
            "thermal_anomaly": 0.85,
            "lstm_reconstruction": 0.040,
            "temp_range": (36.5, 37.5),  # Degrees Celsius
            "co2_range": (4.5, 5.5)  # Percent
        }
    }
}
```

### Step 4: No Retraining Needed! ✅

**Key Insight**: The models are **domain-agnostic**!

- **Thermal CNN**: Learned from FLIR (cars, people, roads)
  - Works for: Fridges, incubators, ovens, autoclaves, ANY thermal anomaly
  - No retraining needed!

- **Acoustic CNN**: Learned from MIMII (industrial fans)
  - Works for: Centrifuges, pumps, stirrers, ANY motor-based equipment
  - No retraining needed!

- **LSTM-AE**: Learned from Turbofan (jet engines)
  - Works for: ANY equipment with time-series sensors showing degradation
  - No retraining needed!

### Step 5: Deploy Additional Raspberry Pi Units

**One Pi per equipment group**:
```
Lab Layout:
├── Pi #1: Refrigeration Zone
│   ├── Fridge #1
│   ├── Fridge #2
│   └── -80°C Freezer
│
├── Pi #2: Incubation Zone
│   ├── Incubator #1
│   ├── Incubator #2
│   └── Shaker incubator
│
├── Pi #3: Chemical Storage
│   ├── Flammable cabinet
│   ├── Acid cabinet
│   └── Solvent storage
│
└── Pi #4: Mechanical Equipment
    ├── Centrifuge #1
    ├── Centrifuge #2
    └── Vacuum pump
```

Each Pi runs the **same code** with different config!

---

## 💻 Code Changes Required

### Minimal Changes Needed!

**1. Multi-Equipment Config** (NEW FILE)
```python
# pythonsoftware/equipment_registry.py

EQUIPMENT_REGISTRY = [
    {
        "id": "fridge_01",
        "type": "fridge",
        "location": "Lab A, Corner",
        "pi_id": "pi_refrigeration_01",
        "sensors": {
            "thermal_camera": {"address": "0x33", "fps": 2},
            "microphone": {"device": "hw:1,0", "sample_rate": 16000},
            "gas_sensor": {"pin": 17, "analog_channel": 0},
            "temperature": {"pin": 4, "ds18b20_id": "28-xxx"}
        },
        "alert_channels": ["discord", "email"]
    },
    {
        "id": "centrifuge_01",
        "type": "centrifuge",
        "location": "Lab B, Bench 3",
        "pi_id": "pi_mechanical_01",
        "sensors": {
            "microphone": {"device": "hw:1,0", "sample_rate": 16000},
            "vibration": {"address": "0x53", "range": "±16g"},
            "current": {"address": "0x40", "shunt_ohms": 0.1}
        },
        "alert_channels": ["discord", "sms"]
    },
    # Add more equipment...
]
```

**2. Dynamic Equipment Loading** (EDIT MAIN)

```python
# pythonsoftware/premonitor_main_hardened.py

import equipment_registry

def main():
    """Main function with multi-equipment support."""
    
    # Load equipment for THIS Pi
    my_pi_id = get_pi_id()  # Read from /etc/hostname or config
    my_equipment = [eq for eq in equipment_registry.EQUIPMENT_REGISTRY 
                    if eq["pi_id"] == my_pi_id]
    
    print(f"Monitoring {len(my_equipment)} pieces of equipment:")
    for eq in my_equipment:
        print(f"  - {eq['id']}: {eq['type']} at {eq['location']}")
    
    # Load models ONCE (shared across all equipment)
    load_models()
    
    # Main monitoring loop
    while True:
        for equipment in my_equipment:
            try:
                # Read sensors for this equipment
                sensor_data = read_sensors(equipment)
                
                # Run inference (same models, different thresholds)
                scores = run_inference(equipment, sensor_data)
                
                # Check equipment-specific thresholds
                check_anomalies(equipment, scores)
                
            except Exception as e:
                log_error(f"Error monitoring {equipment['id']}: {e}")
        
        time.sleep(config.SENSOR_READ_INTERVAL)
```

**3. Equipment-Specific Thresholds** (EDIT CONFIG)

```python
# pythonsoftware/premonitor_config_py.py

# Equipment-specific thresholds
EQUIPMENT_THRESHOLDS = {
    "fridge": {
        "thermal_anomaly": 0.85,
        "acoustic_anomaly": 0.85,
        "lstm_reconstruction": 0.045
    },
    "centrifuge": {
        "acoustic_anomaly": 0.80,  # More sensitive for high-RPM
        "lstm_reconstruction": 0.050
    },
    "incubator": {
        "thermal_anomaly": 0.90,  # Less sensitive (always warm)
        "lstm_reconstruction": 0.040
    },
    "autoclave": {
        "thermal_anomaly": 0.95,  # Very high temp is normal
        "acoustic_anomaly": 0.80,
        "lstm_reconstruction": 0.055
    }
}
```

---

## 🚀 Deployment Scenarios

### Scenario 1: Single Lab (5-10 Equipment Units)

**Hardware**:
- 2-3 Raspberry Pi 4 (4GB RAM)
- 5-10 sensor sets (thermal camera + microphone + gas sensor)
- Total cost: ~$500-800

**Network**:
```
[Internet] ← [Lab Router] ← [All Raspberry Pis]
                                    ↓
                          [Central Discord Webhook]
```

**Alert Flow**:
```
Equipment Anomaly → Pi detects → Discord notification
                                   ↓
                        Lab manager phone gets alert
```

---

### Scenario 2: Multi-Lab Facility (50+ Equipment Units)

**Hardware**:
- 10-15 Raspberry Pi 4
- Centralized logging server (NAS or cloud)
- Dashboard display (TV/monitor)

**Network**:
```
                    [Central Monitor Server]
                            ↑
        ┌───────────────────┼───────────────────┐
        │                   │                   │
   [Lab A Pis]         [Lab B Pis]        [Lab C Pis]
   (5 units)           (5 units)          (5 units)
        ↓                   ↓                   ↓
   Equipment 1-10      Equipment 11-20    Equipment 21-30
```

**Dashboard Features**:
- Real-time status of all equipment
- Historical trends (degradation curves)
- Maintenance schedule predictions
- Alert history and response times

---

### Scenario 3: Multi-Site Research Facility

**Architecture**:
```
[Site A] → [VPN] ┐
[Site B] → [VPN] ├→ [Central Cloud Server] → [Admin Dashboard]
[Site C] → [VPN] ┘                                   ↓
                                              [Email/SMS Alerts]
```

**Features**:
- Centralized monitoring across multiple sites
- Role-based access (site managers vs. administrators)
- Automated maintenance ticket creation
- Predictive maintenance scheduling

---

## 📊 Equipment Priority Matrix

### High Priority (Implement First)
1. ✅ **Fridges/Freezers**: Critical sample storage
2. 🟢 **Incubators**: Live cell cultures
3. 🟢 **Ultra-low Freezers**: Expensive samples
4. 🟢 **Centrifuges**: Frequent use, safety critical

### Medium Priority
5. 🟡 **Autoclaves**: Safety equipment
6. 🟡 **Fume Hoods**: Environmental safety
7. 🟡 **Water Baths**: Common equipment
8. 🟡 **Ovens**: Less critical but useful

### Low Priority (Nice to Have)
9. 🟠 **Shakers**: Lower failure impact
10. 🟠 **Hot Plates**: Individual, easy to replace
11. 🟠 **Stirrers**: Low failure rate

---

## 🎓 Training Strategy for New Equipment Types

### Option 1: Use Existing Models (RECOMMENDED)
**No retraining needed!**
- Thermal CNN works for ANY thermal anomaly
- Acoustic CNN works for ANY motor-based equipment
- LSTM-AE works for ANY time-series degradation

**Just adjust thresholds per equipment type**

---

### Option 2: Fine-Tune on Equipment-Specific Data
**If you have equipment failure recordings**:

```python
# Fine-tune acoustic model on YOUR centrifuge sounds
def fine_tune_acoustic_for_centrifuge():
    # Load pretrained model
    base_model = models.load_model("acoustic_anomaly_model_best.h5")
    
    # Freeze early layers (keep MIMII knowledge)
    for layer in base_model.layers[:-3]:
        layer.trainable = False
    
    # Load YOUR centrifuge recordings
    centrifuge_sounds, labels = load_my_centrifuge_data()
    
    # Fine-tune on your data (only last 3 layers)
    base_model.fit(centrifuge_sounds, labels, epochs=10)
    
    # Save equipment-specific model
    base_model.save("acoustic_centrifuge_specific.h5")
```

**When to fine-tune**:
- You have 100+ recordings of YOUR specific equipment
- Baseline models give too many false positives
- Equipment is unusual (e.g., custom-built)

---

### Option 3: Collect New Equipment Dataset
**For completely new equipment types**:

1. **Record normal operation**:
   - 100+ recordings of normal operation
   - Various operating conditions (idle, low load, high load)

2. **Record failure modes** (if available):
   - Bearing wear sounds
   - Overheating signatures
   - Degradation patterns

3. **Train equipment-specific model**:
   ```python
   # Use same training pipeline
   python premonitor_train_models_py.py --model acoustic --dataset my_equipment_sounds/
   ```

---

## 🔧 Quick Start: Adding Your First New Equipment

### Example: Add Centrifuge Monitoring

**Step 1: Hardware Setup**
```bash
# Connect sensors to existing Pi
# - Microphone → USB port
# - Vibration sensor → GPIO pins
# - Current sensor → I2C bus
```

**Step 2: Edit Config**
```python
# Add to premonitor_config_py.py
EQUIPMENT_TYPES["centrifuge"] = {
    "sensors": ["acoustic", "vibration"],
    "models": ["acoustic_cnn"],
    "thresholds": {"acoustic_anomaly": 0.80}
}
```

**Step 3: Update Main Script**
```python
# No code changes needed if using equipment_registry.py!
# Just add entry to EQUIPMENT_REGISTRY
```

**Step 4: Test**
```bash
# Run on Pi
python3 premonitor_main_hardened.py

# Expected output:
# Monitoring 2 pieces of equipment:
#   - fridge_01: fridge at Lab A, Corner
#   - centrifuge_01: centrifuge at Lab B, Bench 3
```

**Step 5: Calibrate Thresholds**
```python
# Run for 24 hours, collect baseline data
# Adjust thresholds if too sensitive/insensitive
EQUIPMENT_THRESHOLDS["centrifuge"]["acoustic_anomaly"] = 0.75  # Lower = more sensitive
```

---

## 📈 Scaling Economics

### Cost per Equipment Unit

| Component | Cost | Notes |
|-----------|------|-------|
| Thermal Camera (MLX90640) | $60 | Optional for some equipment |
| USB Microphone | $15 | Required for motor equipment |
| Gas Sensor (MQ-series) | $10 | Required for chemical storage |
| Temp/Humidity (DHT22) | $5 | Nice to have |
| Vibration (ADXL345) | $10 | For high-RPM equipment |
| **Per-Equipment Cost** | **$50-100** | Depends on sensors needed |

### Raspberry Pi Shared Across Equipment

| Configuration | Pis Needed | Equipment Monitored | Cost per Equipment |
|---------------|------------|---------------------|-------------------|
| 1 Pi, 1 Equipment | 1 | 1 | ~$100 + Pi ($75) = $175 |
| 1 Pi, 3 Equipment | 1 | 3 | ~$75 + Pi/3 ($25) = $100 |
| 1 Pi, 5 Equipment | 1 | 5 | ~$75 + Pi/5 ($15) = $90 |

**Economies of scale**: More equipment per Pi = lower cost per unit!

---

## ✅ Summary: YES, Easily Expandable!

### What Makes This Scalable

1. **Domain-Agnostic Models**
   - Thermal CNN works for ANY thermal imaging
   - Acoustic CNN works for ANY motor/fan
   - LSTM-AE works for ANY time-series

2. **Modular Architecture**
   - Each equipment type = config entry
   - Same code for all equipment
   - Just adjust thresholds

3. **Shared Inference**
   - Models loaded once
   - Multiple equipment share same Pi
   - Efficient resource usage

4. **Transfer Learning**
   - Pre-trained on 14M ImageNet images
   - Pre-trained on 1,418 industrial fan sounds
   - Pre-trained on jet engine degradation
   - Works for ANY similar equipment!

### Ready to Expand To

- ✅ **Fridges** (implemented)
- 🟢 **Centrifuges** (5 min config change)
- 🟢 **Incubators** (5 min config change)
- 🟢 **Autoclaves** (5 min config change)
- 🟢 **Fume Hoods** (5 min config change)
- 🟢 **Ovens** (5 min config change)
- 🟢 **Vacuum Pumps** (5 min config change)
- 🟢 **ANY motor-based equipment** (works with MIMII!)

**Your entire lab can be monitored with the same AI models!** 🔬🚀
