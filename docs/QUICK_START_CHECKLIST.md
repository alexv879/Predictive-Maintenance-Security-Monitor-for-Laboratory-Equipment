# PREMONITOR Quick Start Checklist

**Use this checklist to quickly deploy PREMONITOR from current state to production.**

---

## ✅ Completed Setup

- [x] Documentation organized into `docs/` structure
- [x] Hardened runtime created (`premonitor_main_hardened.py`)
- [x] Pretrained weight downloader created
- [x] Xception ImageNet weights downloaded (79.8 MB)
- [x] Smoke test models created and exported to TFLite
- [x] Integration guide written
- [x] Training pipeline verified (smoke tests passing)

---

## 📋 Phase 1: Validate Current Setup (30 min)

### Step 1.1: Test Hardened Runtime
```powershell
cd D:\PREMONITOR
python pythonsoftware\premonitor_main_hardened.py
```
**Expected**: Runs with structured logging, loads smoke test models  
**If fails**: Check import paths in config/alert_manager/mock_hardware modules

- [ ] Runtime starts without errors
- [ ] Logging output shows INFO messages
- [ ] Models load successfully
- [ ] Press Ctrl+C to test graceful shutdown

---

### Step 1.2: Verify Pretrained Weights
```powershell
python scripts\fetch_pretrained_weights.py --model list
ls models\pretrained\
```
**Expected**: Shows Xception downloaded, MobileNetV2/YAMNet alternatives noted

- [ ] Xception file exists (79.8 MB)
- [ ] Registry.json tracks downloads

---

### Step 1.3: Check Datasets
```powershell
python scripts\check_datasets.py --verbose
```
**Expected**: ESC-50, UrbanSound8K, AAU VAP Trimodal verified

- [ ] ESC-50: 2,000 files
- [ ] UrbanSound8K: 8,732 files
- [ ] AAU VAP Trimodal: 11,537 thermal images
- [ ] MIMII: [MISSING] - optional for now

---

## 📋 Phase 2: Integrate Pretrained Weights (2 hours)

### Step 2.1: Modify train.py

Add to `train.py` after imports:
```python
def build_thermal_model_with_pretrained(config):
    """Build thermal model with Xception backbone"""
    from tensorflow.keras.models import load_model
    from tensorflow.keras.applications import Xception
    from tensorflow.keras.layers import GlobalAveragePooling2D, Dense, Dropout
    from tensorflow.keras import Sequential
    
    # Try loading local Xception first
    xception_path = 'models/pretrained/xception_imagenet_notop.h5'
    if os.path.exists(xception_path):
        logger.info(f"Loading Xception from {xception_path}")
        base = load_model(xception_path)
    else:
        logger.info("Downloading Xception from Keras")
        base = Xception(input_shape=(224, 224, 3), include_top=False, weights='imagenet')
    
    # Freeze backbone
    base.trainable = False
    logger.info(f"Xception backbone frozen: {len(base.layers)} layers")
    
    # Add custom head
    model = Sequential([
        base,
        GlobalAveragePooling2D(name='gap'),
        Dense(256, activation='relu', name='fc1'),
        Dropout(0.5, name='dropout1'),
        Dense(1, activation='sigmoid', name='output')
    ])
    
    return model
```

Update `train_thermal_model_smoke()` method:
```python
# Replace model creation with:
model = build_thermal_model_with_pretrained(config)
```

- [ ] Code added to train.py
- [ ] No syntax errors (check with `python -m py_compile train.py`)

---

### Step 2.2: Test Smoke Test with Pretrained
```powershell
python train.py --mode smoke_test --model thermal
```
**Expected**: Loads Xception, trains for 2 epochs on synthetic data (1-2 min)

**Look for in logs**:
```
INFO:__main__:Loading Xception from models/pretrained/xception_imagenet_notop.h5
INFO:__main__:Xception backbone frozen: 126 layers
INFO:__main__:Training thermal model (smoke test)...
Epoch 1/2
...
```

- [ ] Xception loads successfully
- [ ] Training completes 2 epochs
- [ ] Model saved to `models/checkpoints/thermal_smoke_test.h5`
- [ ] Training report JSON created

---

### Step 2.3: Add YAMNet for Acoustic (Optional)
```python
def build_acoustic_model_with_yamnet(config):
    """Build acoustic model with YAMNet embeddings"""
    import tensorflow_hub as hub
    from tensorflow.keras import Sequential
    from tensorflow.keras.layers import Input, Dense, Dropout
    
    # Load YAMNet from TF Hub
    yamnet_layer = hub.KerasLayer(
        'https://tfhub.dev/google/yamnet/1',
        trainable=False,
        arguments=dict(output_key='embedding')
    )
    
    model = Sequential([
        Input(shape=(None,), name='audio_input'),
        yamnet_layer,
        Dense(512, activation='relu', name='fc1'),
        Dropout(0.5, name='dropout1'),
        Dense(256, activation='relu', name='fc2'),
        Dense(1, activation='sigmoid', name='output')
    ])
    
    return model
```

```powershell
python train.py --mode smoke_test --model acoustic
```

- [ ] YAMNet loads from TF Hub (first time takes ~30s)
- [ ] Training completes successfully

---

## 📋 Phase 3: Full Training (4-8 hours GPU time)

### Step 3.1: Prepare Training Config
Edit `training_config.yaml`:
```yaml
thermal_model:
  use_pretrained: true
  backbone: 'xception'
  input_shape: [224, 224, 3]
  epochs: 50
  batch_size: 32
  learning_rate: 0.001

acoustic_model:
  use_pretrained: true
  backbone: 'yamnet'
  epochs: 50
  batch_size: 16
  learning_rate: 0.0001
```

- [ ] Config updated with pretrained flags
- [ ] Epochs set to 50
- [ ] Learning rates appropriate

---

### Step 3.2: Train Thermal Model
```powershell
python train.py --mode full --model thermal --epochs 50
```
**Time**: ~2-4 hours on GPU  
**Output**: `models/checkpoints/thermal_classifier_best.h5`

- [ ] Training starts without errors
- [ ] Validation accuracy > 0.85 after 10 epochs
- [ ] Best model checkpoint saved
- [ ] Training report JSON created

---

### Step 3.3: Train Acoustic Model
```powershell
python train.py --mode full --model acoustic --epochs 50
```
**Time**: ~2-4 hours on GPU  
**Output**: `models/checkpoints/acoustic_anomaly_model_best.h5`

- [ ] Training completes
- [ ] Validation accuracy > 0.80
- [ ] Best model saved

---

## 📋 Phase 4: Export to TFLite (30 min)

### Step 4.1: Export Thermal Model
```powershell
python export_tflite.py --model thermal_classifier_best --quantize int8 --calibration-samples 100
```
**Output**: `models/exported/thermal_anomaly_model_int8.tflite`

- [ ] INT8 model exported (~23 MB)
- [ ] Export report created
- [ ] No quantization errors

---

### Step 4.2: Export Acoustic Model
```powershell
python export_tflite.py --model acoustic_anomaly_model_best --quantize int8 --calibration-samples 100
```
**Output**: `models/exported/acoustic_anomaly_model_int8.tflite`

- [ ] INT8 model exported (~2-5 MB)
- [ ] Export report created

---

### Step 4.3: Validate Exported Models
```powershell
python pi_smoke_test.py
```
**Expected**: Runs inference with TFLite INT8 models, shows predictions

- [ ] Thermal inference < 150ms per frame
- [ ] Acoustic inference < 100ms per sample
- [ ] Predictions reasonable (0.0-1.0 range)

---

## 📋 Phase 5: Raspberry Pi Deployment (1 hour)

### Step 5.1: Prepare Pi
```bash
# On Raspberry Pi
sudo apt update
sudo apt install python3-pip
pip3 install tflite-runtime numpy
```

- [ ] Pi has Python 3.7+
- [ ] tflite-runtime installed
- [ ] At least 1GB free storage

---

### Step 5.2: Copy Files
```powershell
# From Windows (using pscp or WinSCP)
pscp -r pythonsoftware pi@raspberrypi.local:/home/pi/premonitor/
pscp -r models/exported/*.tflite pi@raspberrypi.local:/home/pi/premonitor/models/
pscp pythonsoftware/premonitor_*.py pi@raspberrypi.local:/home/pi/premonitor/pythonsoftware/
```

- [ ] pythonsoftware/ copied
- [ ] TFLite models copied
- [ ] Config files copied

---

### Step 5.3: Test on Pi
```bash
# On Raspberry Pi
cd /home/pi/premonitor
python3 pythonsoftware/premonitor_main_hardened.py
```
**Expected**: Runs with logging, loads INT8 models, starts main loop

- [ ] No import errors
- [ ] Models load in < 5 seconds
- [ ] Logging shows INFO messages
- [ ] Graceful shutdown with Ctrl+C

---

### Step 5.4: Create Systemd Service
```bash
# On Pi
sudo nano /etc/systemd/system/premonitor.service
```

Paste:
```ini
[Unit]
Description=PREMONITOR Lab Safety Monitor
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/premonitor
ExecStart=/usr/bin/python3 pythonsoftware/premonitor_main_hardened.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable premonitor
sudo systemctl start premonitor
sudo systemctl status premonitor
```

- [ ] Service file created
- [ ] Service enabled (starts on boot)
- [ ] Service running (status shows "active")
- [ ] Logs visible with `journalctl -u premonitor -f`

---

## 📋 Phase 6: Production Validation (2 hours)

### Step 6.1: Monitor Logs
```bash
# On Pi
sudo journalctl -u premonitor -f
```
**Watch for**:
- INFO messages every 5 seconds (sensor read interval)
- Thermal inference predictions
- Acoustic inference predictions
- No ERROR or CRITICAL messages

- [ ] Logs flowing continuously
- [ ] No errors for 10+ minutes
- [ ] Predictions reasonable

---

### Step 6.2: Test Alert System
```bash
# On Pi - simulate high temperature
# Edit config temporarily to lower threshold
nano pythonsoftware/premonitor_config_py.py
# Change THERMAL_THRESHOLD to 0.3 (normally 0.7)
# Restart service
sudo systemctl restart premonitor
```

- [ ] Alert triggered when threshold exceeded
- [ ] Email sent (if configured)
- [ ] Log shows CRITICAL message
- [ ] Alert cooldown works (doesn't spam)

---

### Step 6.3: Stress Test
```bash
# Run for 24 hours
sudo journalctl -u premonitor -f > /tmp/premonitor_24h.log
```
**Monitor**:
- Memory usage: `htop` (should stay < 200 MB)
- CPU usage: Should be < 30% average
- No memory leaks (memory stable over time)
- Log file size manageable (< 100 MB/day)

- [ ] 24-hour test completed
- [ ] No crashes or restarts
- [ ] Memory stable
- [ ] Logs rotating properly

---

## 📋 Phase 7: Connect Real Sensors (4 hours)

### Step 7.1: Hardware Setup
**Thermal Camera**: MLX90640 (32×24 thermal array)
```bash
pip3 install adafruit-circuitpython-mlx90640
```

**Microphone**: USB or I2S microphone
```bash
pip3 install pyaudio sounddevice
```

- [ ] Thermal camera connected via I2C
- [ ] Microphone detected: `arecord -l`
- [ ] Test thermal: `i2cdetect -y 1` shows 0x33

---

### Step 7.2: Update Hardware Driver
Edit `pythonsoftware/premonitor_hardware_drivers_py_(finalized).py`:
- Replace mock thermal with MLX90640 code
- Replace mock microphone with real audio capture
- Test each sensor independently

- [ ] Thermal camera returns 32×24 frames
- [ ] Microphone captures 16kHz audio
- [ ] Drivers integrated into main loop

---

### Step 7.3: Calibration
Run calibration mode to set baseline:
```python
python3 scripts/calibrate_sensors.py --thermal --acoustic --duration 300
```
**Captures**: 5 minutes of normal operation data

- [ ] Baseline thermal range captured
- [ ] Background noise profile captured
- [ ] Thresholds adjusted based on environment

---

## 📋 Final Checks

### Documentation
- [ ] All docs in `docs/` folder
- [ ] README updated with deployment instructions
- [ ] Training reports reviewed
- [ ] Export reports verified

### Code Quality
- [ ] No lint errors in main modules
- [ ] All tests passing: `python tests/run_all_tests.py`
- [ ] Config values appropriate for lab environment
- [ ] Logging levels set correctly (INFO for production)

### Performance
- [ ] Thermal inference < 150ms (INT8 on Pi)
- [ ] Acoustic inference < 100ms (INT8 on Pi)
- [ ] Total loop time < 5 seconds
- [ ] Memory usage < 200 MB

### Alerts
- [ ] Email credentials configured
- [ ] SMS gateway tested (optional)
- [ ] Alert thresholds calibrated
- [ ] Cooldown periods appropriate (300s default)

### Compliance
- [ ] Audit logs enabled
- [ ] Log retention policy set (90 days)
- [ ] Backup strategy for logs
- [ ] Anomaly reports generated daily

---

## 🚀 Production Ready!

When all checkboxes are complete, PREMONITOR is ready for production deployment.

**Monitoring**:
```bash
# View real-time logs
sudo journalctl -u premonitor -f

# Check service status
sudo systemctl status premonitor

# View resource usage
htop

# Check recent alerts
tail -n 50 logs/alerts.log
```

**Maintenance Schedule**:
- Daily: Check logs for anomalies
- Weekly: Review alert accuracy, adjust thresholds
- Monthly: Retrain models with new data
- Quarterly: Update dependencies, security patches

---

**Last Updated**: October 29, 2025  
**Version**: 2.0 (Hardened with Pretrained Weights)
