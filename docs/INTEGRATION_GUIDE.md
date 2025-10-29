# PREMONITOR Integration Guide
## Production-Ready Setup with Pretrained Weights

**Date**: October 29, 2025  
**Version**: 2.0 (Hardened)

---

## Overview

This guide covers the complete setup for PREMONITOR with:
1. Runtime hardening (logging, TFLite fallback, robust inference)
2. Pretrained weights integration
3. Organized documentation structure
4. Production deployment checklist

---

## 1. File Organization

### New Structure
```
PREMONITOR/
├── docs/                          # All documentation
│   ├── README.md                  # Main project README
│   ├── TRAINING_AND_DEPLOYMENT_GUIDE.md
│   ├── RESEARCH_SUMMARY.md
│   └── reports/                   # Generated reports
│       ├── VERIFICATION_REPORT.md
│       ├── TRAINING_EXECUTION_REPORT.md
│       └── FINAL_VERIFICATION_SUMMARY.md
├── models/
│   ├── pretrained/                # Downloaded pretrained weights
│   │   ├── registry.json
│   │   ├── mobilenetv2_imagenet.h5
│   │   ├── xception_imagenet_notop.h5
│   │   └── yamnet_audioset/
│   ├── checkpoints/               # Training checkpoints
│   └── exported/                  # TFLite models for deployment
├── pythonsoftware/
│   ├── premonitor_main_hardened.py    # NEW: Production-ready main
│   └── ...                        # Other modules
└── scripts/
    ├── fetch_pretrained_weights.py    # NEW: Weight downloader
    └── organize_docs.ps1              # NEW: Doc organizer
```

### Organizing Existing Documentation

Run the PowerShell script to move files:
```powershell
cd D:\PREMONITOR
.\scripts\organize_docs.ps1
```

Or manually:
```powershell
# Move main docs
Move-Item README.md docs\
Move-Item TRAINING_AND_DEPLOYMENT_GUIDE.md docs\
Move-Item RESEARCH_SUMMARY.md docs\

# Move reports
Move-Item *REPORT*.md docs\reports\
Move-Item CHANGELOG.md docs\reports\
```

---

## 2. Runtime Hardening Features

### New Hardened Main Module
**File**: `pythonsoftware/premonitor_main_hardened.py`

**Key Improvements**:

1. **Structured Logging**
   - Replace `print()` with `logging` module
   - Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
   - Output to both console and file
   
2. **TFLite Runtime Fallback**
   ```python
   # Tries tflite_runtime first (lighter for Pi)
   # Falls back to tensorflow.lite if unavailable
   ```

3. **Robust Shape/Dtype Handling**
   - Handles quantized models (uint8, int8)
   - Automatic dequantization of outputs
   - Flexible shape matching (handles -1 dimensions)

4. **Startup Validation**
   - Checks model file existence
   - Validates configuration
   - Creates required directories
   - Returns clear error messages

5. **Graceful Shutdown**
   - Signal handlers for SIGINT/SIGTERM
   - Cleanup before exit
   - Logs total cycles completed

### Using the Hardened Version

**For Development/Testing**:
```python
# Run directly
python pythonsoftware/premonitor_main_hardened.py
```

**For Production on Raspberry Pi**:
```bash
# Install tflite_runtime (lighter than full TensorFlow)
pip3 install tflite-runtime

# Run as service (see systemd section below)
```

---

## 3. Pretrained Weights Integration

### Download Pretrained Models

**List Available Models**:
```powershell
python scripts\fetch_pretrained_weights.py --model list
```

**Download Specific Model**:
```powershell
# Thermal backbone (MobileNetV2 - 14 MB, fast)
python scripts\fetch_pretrained_weights.py --model thermal_mobilenetv2

# Thermal backbone (Xception - 83 MB, more accurate)
python scripts\fetch_pretrained_weights.py --model thermal_xception

# Acoustic model (YAMNet - 7 MB)
python scripts\fetch_pretrained_weights.py --model acoustic_yamnet
```

**Download All Models**:
```powershell
python scripts\fetch_pretrained_weights.py --model all
```

### Pretrained Model Registry

| Model Key | Name | Size | Use Case | License |
|-----------|------|------|----------|---------|
| `thermal_mobilenetv2` | MobileNetV2 ImageNet | 14 MB | Fast thermal encoder | Apache 2.0 |
| `thermal_xception` | Xception ImageNet | 83 MB | High-accuracy thermal | MIT |
| `acoustic_yamnet` | YAMNet AudioSet | 7 MB | Sound event detection | Apache 2.0 |

### Integration with Training

The training script automatically detects pretrained weights in `models/pretrained/`:

```yaml
# In training_config.yaml
thermal_model:
  use_pretrained: true
  pretrained_weights: "models/pretrained/mobilenetv2_imagenet.h5"
  freeze_backbone: true  # Start with frozen, unfreeze later
```

**Training Workflow**:
1. Load pretrained backbone (e.g., MobileNetV2)
2. Replace top layers with anomaly detection head
3. Freeze backbone initially
4. Train on your dataset
5. Optionally unfreeze and fine-tune

---

## 4. Running Tests

### Dataset Validation
```powershell
python scripts\check_datasets.py --verbose
```

### Training Smoke Test
```powershell
# Test thermal model (synthetic data)
python train.py --mode smoke_test --model thermal

# Test acoustic model (synthetic data)
python train.py --mode smoke_test --model acoustic

# Test both
python train.py --mode smoke_test --model all
```

### Model Export Test
```powershell
# Export smoke test models to TFLite
python export_tflite.py --model thermal_smoke_test --quantize all
python export_tflite.py --model acoustic_smoke_test --quantize all
```

### Pi Smoke Test (Inference Validation)
```powershell
python pi_smoke_test.py
```

### Full Test Suite
```powershell
python tests\run_all_tests.py
```

---

## 5. Production Deployment Checklist

### Pre-Deployment

- [ ] Download pretrained weights
  ```powershell
  python scripts\fetch_pretrained_weights.py --model all
  ```

- [ ] Train models with real datasets
  ```powershell
  python train.py --mode full --model all
  ```

- [ ] Export to INT8 TFLite
  ```powershell
  python export_tflite.py --model thermal_classifier_best --quantize int8
  python export_tflite.py --model acoustic_anomaly_model_best --quantize int8
  ```

- [ ] Validate exported models
  ```powershell
  python pi_smoke_test.py
  ```

- [ ] Run full test suite
  ```powershell
  python tests\run_all_tests.py
  ```

### Raspberry Pi Setup

1. **Install Dependencies**
   ```bash
   # Minimal runtime (recommended)
   pip3 install tflite-runtime numpy

   # Or full TensorFlow (larger)
   pip3 install tensorflow
   ```

2. **Copy Files to Pi**
   ```powershell
   # From Windows (using pscp or scp)
   pscp -r pythonsoftware pi@raspberrypi:/home/pi/premonitor/
   pscp -r models/exported/*.tflite pi@raspberrypi:/home/pi/premonitor/models/
   ```

3. **Configure Systemd Service**
   ```bash
   # On Raspberry Pi
   sudo nano /etc/systemd/system/premonitor.service
   ```
   
   ```ini
   [Unit]
   Description=PREMONITOR Anomaly Detection System
   After=network.target

   [Service]
   Type=simple
   User=pi
   WorkingDirectory=/home/pi/premonitor
   ExecStart=/usr/bin/python3 pythonsoftware/premonitor_main_hardened.py
   Restart=on-failure
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

4. **Enable and Start Service**
   ```bash
   sudo systemctl enable premonitor
   sudo systemctl start premonitor
   sudo systemctl status premonitor
   ```

5. **View Logs**
   ```bash
   sudo journalctl -u premonitor -f
   ```

---

## 6. Configuration Updates

### Update Model Paths in Config

Edit `pythonsoftware/premonitor_config_py.py`:

```python
# Use INT8 quantized models for production
THERMAL_MODEL_PATH = os.path.join(MODEL_DIR, "thermal_anomaly_model_int8.tflite")
ACOUSTIC_MODEL_PATH = os.path.join(MODEL_DIR, "acoustic_anomaly_model_int8.tflite")
```

### Logging Configuration

```python
# In config.py
DEBUG_MODE = False  # Set to False for production
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 5  # Keep 5 rotated logs
```

---

## 7. Performance Expectations

### Model Sizes (After INT8 Quantization)

| Model | Float32 | INT8 | Reduction |
|-------|---------|------|-----------|
| Thermal (MobileNetV2) | ~14 MB | ~3.5 MB | 75% |
| Acoustic (CNN) | ~8 MB | ~2 MB | 75% |

### Inference Speed (Raspberry Pi 4)

| Model | Float32 | INT8 |
|-------|---------|------|
| Thermal | ~200ms | ~50ms |
| Acoustic | ~150ms | ~40ms |

### Memory Usage

- **Float32 models**: ~150 MB RAM
- **INT8 models**: ~80 MB RAM
- **Recommended**: Pi 4 with 2GB+ RAM

---

## 8. Troubleshooting

### Model Loading Errors

**Error**: `"No tflite interpreter available"`
```bash
# Solution: Install tflite_runtime
pip3 install tflite-runtime
```

**Error**: `"Model file not found"`
```bash
# Check model paths
ls -l models/exported/

# Verify config.py paths match actual files
```

### Shape Mismatch Errors

The hardened version handles this automatically, but if you see warnings:
```
Input shape mismatch: got (224, 224, 3), expected (224, 224, 3)
```

Check that:
1. Input images are resized to model's expected size
2. Channels are correct (RGB=3, grayscale=1)

### Quantization Issues

**Error**: `"quantization parameters not found"`
- This means the model wasn't properly quantized
- Re-export with representative dataset:
  ```powershell
  python export_tflite.py --model MODEL_NAME --quantize int8 --calibration-samples 100
  ```

---

## 9. Next Steps

### Immediate Actions

1. **Organize documentation**
   ```powershell
   .\scripts\organize_docs.ps1
   ```

2. **Download pretrained weights**
   ```powershell
   python scripts\fetch_pretrained_weights.py --model all
   ```

3. **Test hardened runtime**
   ```powershell
   python pythonsoftware\premonitor_main_hardened.py
   ```

### For Full Deployment

1. Download MIMII dataset (acoustic training)
2. Create labeled thermal anomaly dataset
3. Run full training with pretrained weights
4. Export INT8 TFLite models
5. Deploy to Raspberry Pi with systemd service

---

## 10. Quick Reference Commands

```powershell
# Documentation
.\scripts\organize_docs.ps1

# Pretrained weights
python scripts\fetch_pretrained_weights.py --model list
python scripts\fetch_pretrained_weights.py --model all

# Training
python train.py --mode smoke_test --model all
python train.py --mode full --model thermal

# Export
python export_tflite.py --model thermal_classifier_best --quantize int8

# Testing
python scripts\check_datasets.py --verbose
python pi_smoke_test.py
python tests\run_all_tests.py

# Run hardened main
python pythonsoftware\premonitor_main_hardened.py
```

---

## Support & Documentation

- Main documentation: `docs/README.md`
- Training guide: `docs/TRAINING_AND_DEPLOYMENT_GUIDE.md`
- Research summary: `docs/RESEARCH_SUMMARY.md`
- Reports: `docs/reports/`

---

**End of Integration Guide**
