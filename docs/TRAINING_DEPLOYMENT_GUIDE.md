# PREMONITOR Training & Deployment Guide

**Last Updated**: 2025-10-29  
**Purpose**: Complete workflow from dataset verification → training → Raspberry Pi deployment

---

## 📋 Overview

PREMONITOR uses a **Train on PC → Deploy on Pi** architecture:

1. **Development PC**: Train models on 38,000+ real samples using GPU
2. **Raspberry Pi**: Run inference with INT8 TFLite models (10x smaller, 4x faster)

**Key Principle**: Only learned weights go to Pi, NOT datasets!

---

## 🚀 Quick Start (3 Steps)

### Step 1: Verify Datasets (2 minutes)

```powershell
cd d:\PREMONITOR\pythonsoftware
python verify_datasets.py
```

**Expected Output**:
```
✓ ALL CRITICAL DATASETS READY!
  - MIMII: 1,418+ fan sounds (normal/abnormal)
  - FLIR: 21,488 thermal images
  - ESC-50: 2,000 environmental sounds
```

If any dataset shows `✗ MISSING`, extract it first (see Troubleshooting section).

---

### Step 2: Train Models (4-8 hours GPU)

**Train Thermal Model** (FLIR pre-training + AAU VAP fine-tuning):
```powershell
cd d:\PREMONITOR\pythonsoftware
python premonitor_train_models_py.py --model thermal
```

**Train Acoustic Model** (MIMII machine sounds + ESC-50 environmental):
```powershell
python premonitor_train_models_py.py --model acoustic
```

**Outputs**:
- `models/thermal_classifier_best.h5` (full Keras model, ~50 MB)
- `models/acoustic_anomaly_model_best.h5` (full Keras model, ~30 MB)

---

### Step 3: Export to TFLite (1 minute)

```powershell
python export_tflite.py --model thermal
python export_tflite.py --model acoustic
```

**Outputs** (ready for Raspberry Pi):
- `models/thermal_anomaly.tflite` (INT8 quantized, ~5 MB)
- `models/acoustic_anomaly.tflite` (INT8 quantized, ~3 MB)

**Deploy to Pi**:
```powershell
# Copy only .tflite files and Python code (NO datasets!)
scp models/*.tflite pi@raspberrypi:/home/pi/premonitor/models/
scp pythonsoftware/*.py pi@raspberrypi:/home/pi/premonitor/
```

---

## 📊 Dataset Inventory

### Audio Datasets (for Acoustic Model)

| Dataset | Samples | Use Case | Priority |
|---------|---------|----------|----------|
| **MIMII** | 1,418+ | Primary training (machine anomalies) | 🔴 CRITICAL |
| **ESC-50** | 2,000 | Environmental sound pre-training | 🔴 CRITICAL |
| **UrbanSound8K** | 8,732 | Negative examples (non-anomaly) | 🟡 Optional |

### Thermal Datasets (for Thermal Model)

| Dataset | Samples | Use Case | Priority |
|---------|---------|----------|----------|
| **FLIR ADAS v2** | 21,488 | Pre-training (self-supervised) | 🔴 CRITICAL |
| **AAU VAP Trimodal** | 14,000+ | Fine-tuning (labeled anomalies) | 🟡 Recommended |

### Time-Series Datasets (for LSTM-AE)

| Dataset | Samples | Use Case | Priority |
|---------|---------|----------|----------|
| **Turbofan** | Unknown | Equipment degradation prediction | 🟡 Future V2 |
| **SECOM** | Unknown | Semiconductor anomaly detection | 🟢 Research |
| **CASAS Aruba** | Unknown | Activity pattern recognition | 🟢 Research |

---

## 🔧 Detailed Training Process

### Thermal Model (2-Stage Training)

**Stage 1: Self-Supervised Pre-training (FLIR - 21,488 images)**
- Method: SimSiam contrastive learning
- Goal: Learn robust thermal image features
- Duration: ~3 hours (50 epochs, GPU required)
- Output: `thermal_encoder_pretrained.h5`

**Stage 2: Supervised Fine-tuning (AAU VAP - labeled data)**
- Method: Binary classification (normal vs anomaly)
- Goal: Detect hot spots, fire, people
- Duration: ~1 hour (25 epochs)
- Output: `thermal_classifier_best.h5`

**Command**:
```powershell
python premonitor_train_models_py.py --model thermal
```

**What Happens**:
1. Loads 21,488 FLIR thermal images
2. Trains encoder using SimSiam (learns thermal patterns)
3. Freezes encoder weights
4. Loads AAU VAP labeled data (Scene 1 + Scene 2)
5. Trains classification head
6. Saves best model based on validation accuracy

---

### Acoustic Model (Single-Stage Training)

**Training (MIMII + ESC-50)**
- Method: Binary classification with environmental filtering
- Goal: Detect abnormal machine sounds (fridge failure)
- Duration: ~2 hours (30 epochs)
- Output: `acoustic_anomaly_model_best.h5`

**Command**:
```powershell
python premonitor_train_models_py.py --model acoustic
```

**What Happens**:
1. Loads MIMII fan sounds (1,011 normal + 407 abnormal)
2. Loads ESC-50 environmental sounds (2,000 samples)
3. Combines datasets with 3-class labels:
   - 0 = Normal machine sound
   - 1 = Abnormal machine sound (TARGET)
   - 2 = Environmental sound (ignore)
4. Trains CNN to distinguish machine anomalies
5. Saves best model based on validation accuracy

---

## 📦 Export to TFLite (Raspberry Pi Deployment)

### Why TFLite?

| Format | Size | Speed | Raspberry Pi? |
|--------|------|-------|---------------|
| Keras (.h5) | 50 MB | 1x | ❌ Too slow |
| TFLite (FP32) | 15 MB | 2x | ⚠️ Still slow |
| **TFLite (INT8)** | **5 MB** | **4x** | ✅ **PERFECT** |

### Export Process

```powershell
cd d:\PREMONITOR\pythonsoftware
python export_tflite.py --model thermal --quantize int8
python export_tflite.py --model acoustic --quantize int8
```

**Quantization**: Converts 32-bit floats → 8-bit integers
- **Pros**: 4x faster, 10x smaller, runs on Pi
- **Cons**: ~1% accuracy drop (acceptable)

**Output Files**:
- `models/thermal_anomaly.tflite` (~5 MB)
- `models/acoustic_anomaly.tflite` (~3 MB)

---

## 🍇 Raspberry Pi Deployment

### What to Copy to Pi

**✅ COPY**:
- `models/*.tflite` (learned weights only!)
- `pythonsoftware/premonitor_main_hardened.py`
- `pythonsoftware/premonitor_config_py.py`
- `pythonsoftware/premonitor_alert_manager_py.py`
- `pythonsoftware/premonitor_hardware_drivers_py_(finalized).py`

**❌ DO NOT COPY**:
- `datasets/` (30 GB - stays on PC!)
- `models/*.h5` (too large, use .tflite instead)
- Training scripts (train_models.py, model_blueprints.py, utils.py)

### Pi Setup Commands

```bash
# On Raspberry Pi
mkdir -p /home/pi/premonitor/models
mkdir -p /home/pi/premonitor/pythonsoftware

# From PC (PowerShell)
scp models/*.tflite pi@raspberrypi:/home/pi/premonitor/models/
scp pythonsoftware/premonitor_*.py pi@raspberrypi:/home/pi/premonitor/pythonsoftware/

# On Pi - Install TFLite runtime (lightweight!)
pip3 install tflite-runtime
pip3 install numpy

# Test inference
cd /home/pi/premonitor/pythonsoftware
python3 premonitor_main_hardened.py
```

---

## 🔍 Troubleshooting

### Dataset Not Found

**Problem**: `verify_datasets.py` shows `✗ MISSING`

**Solution**:
```powershell
# Extract compressed datasets
cd "d:\PREMONITOR\datasets\time-series anomaly detection datasets"
Expand-Archive "17.+Turbofan+Engine+Degradation+Simulation+Data+Set+2.zip" -DestinationPath "."
Expand-Archive "secom.zip" -DestinationPath "."
Expand-Archive "CASAS aruba dataset.zip" -DestinationPath "."

# Then extract nested archives
cd "CASAS aruba dataset"
Expand-Archive "data.zip" -DestinationPath "."
Expand-Archive "labeled_data.zip" -DestinationPath "."
```

---

### Training Errors

**Problem**: `Import "tensorflow" could not be resolved`

**Solution**:
```powershell
# Install TensorFlow with GPU support
pip install tensorflow-gpu==2.13.0  # For CUDA 11.8
# OR for CPU-only (slower)
pip install tensorflow==2.13.0

# Install other dependencies
pip install librosa pandas tqdm
```

---

### Out of Memory

**Problem**: Training crashes with OOM error

**Solution**:
```python
# In premonitor_train_models_py.py, reduce batch size:
train_thermal_model(epochs=50, batch_size=16)  # Was 32
train_acoustic_model(epochs=30, batch_size=32)  # Was 64
```

---

### Model Accuracy Too Low

**Problem**: Validation accuracy < 80%

**Solution**:
1. **More epochs**: Increase from 50 → 100
2. **Data augmentation**: Already enabled in utils.py
3. **Learning rate**: Try `0.0001` instead of `0.001`
4. **Check labels**: Verify annotations in AAU VAP dataset

---

## 📈 Expected Training Results

### Thermal Model

| Metric | Stage 1 (Pre-training) | Stage 2 (Fine-tuning) |
|--------|------------------------|----------------------|
| Dataset | FLIR (21,488) | AAU VAP (14,000+) |
| Loss | ~0.15 (SimSiam) | ~0.20 (Binary) |
| Accuracy | N/A (unsupervised) | ~92-95% |
| Duration | 3 hours | 1 hour |

### Acoustic Model

| Metric | Value |
|--------|-------|
| Dataset | MIMII (1,418) + ESC-50 (2,000) |
| Training Accuracy | ~95% |
| Validation Accuracy | ~88-92% |
| Duration | 2 hours |

---

## 🎯 Validation Testing

### Before Deploying to Pi

```python
# Test inference on PC first
import tensorflow as tf
import numpy as np

# Load TFLite model
interpreter = tf.lite.Interpreter(model_path='models/thermal_anomaly.tflite')
interpreter.allocate_tensors()

# Get input/output details
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# Test with random data (replace with real image)
test_input = np.random.rand(1, 96, 96, 3).astype(np.float32)
interpreter.set_tensor(input_details[0]['index'], test_input)
interpreter.invoke()
output = interpreter.get_tensor(output_details[0]['index'])

print(f"Anomaly score: {output[0][0]:.4f}")
# Expected: value between 0.0 (normal) and 1.0 (anomaly)
```

---

## 📚 Next Steps

### After Successful Training

1. ✅ Verify models with `verify_datasets.py`
2. ✅ Train thermal and acoustic models
3. ✅ Export to TFLite (INT8 quantized)
4. ✅ Test inference on PC
5. ✅ Deploy to Raspberry Pi
6. ✅ Run real-time monitoring

### Future Enhancements (V2)

- **LSTM Autoencoder**: Train on Turbofan dataset for fridge degradation prediction
- **Multi-modal Fusion**: Combine RGB + Thermal from AAU VAP
- **Online Learning**: Update models with new lab-specific data
- **Edge TPU**: Use Coral USB Accelerator for 10x faster inference

---

## 📞 Support

**Issues**: Check `logs/training.log` for errors  
**Questions**: Review `docs/DATASET_INVENTORY.md` for dataset details  
**Updates**: All training outputs saved to `models/` directory

---

**REMEMBER**: Datasets stay on PC, only .tflite weights go to Pi! 🍇
