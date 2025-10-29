# 🚀 PREMONITOR Quick Reference Card

**Last Updated**: 2025-10-29

---

## ⚡ Quick Commands

### 1. Extract All Datasets (Run Once)
```powershell
cd d:\PREMONITOR\scripts
.\extract_all_datasets.ps1
```

### 2. Verify Datasets
```powershell
cd d:\PREMONITOR\pythonsoftware
python verify_datasets.py
```

### 3. Train Models
```powershell
# Thermal Model (4 hours GPU)
python premonitor_train_models_py.py --model thermal

# Acoustic Model (2 hours GPU)
python premonitor_train_models_py.py --model acoustic
```

### 4. Export to TFLite
```powershell
python export_tflite.py --model thermal --quantize int8
python export_tflite.py --model acoustic --quantize int8
```

### 5. Deploy to Raspberry Pi
```powershell
# Copy ONLY .tflite files (NOT datasets!)
scp models/*.tflite pi@raspberrypi:/home/pi/premonitor/models/
scp pythonsoftware/premonitor_*.py pi@raspberrypi:/home/pi/premonitor/
```

---

## 📊 Dataset Quick Reference

| Dataset | Location | Files | Use |
|---------|----------|-------|-----|
| **MIMII** | `datasets audio/Mimii/` | 1,418 | Fridge sounds |
| **ESC-50** | `datasets audio/ESC-50-master/` | 2,000 | Environmental |
| **FLIR** | `thermal camera dataset/FLIR_ADAS_v2/` | 21,488 | Thermal pre-train |
| **AAU VAP** | `thermal camera dataset/trimodaldataset/` | 14,000+ | Thermal fine-tune |
| **Turbofan** | `time-series.../17.+Turbofan.../` | TBD | Future LSTM-AE |

---

## 🎯 Training Outputs

### What Gets Created

| File | Size | Purpose | Deploy to Pi? |
|------|------|---------|---------------|
| `thermal_encoder_pretrained.h5` | ~40 MB | Pre-trained encoder | ❌ No |
| `thermal_classifier_best.h5` | ~50 MB | Full thermal model | ❌ No |
| `acoustic_anomaly_model_best.h5` | ~30 MB | Full acoustic model | ❌ No |
| `thermal_anomaly.tflite` | ~5 MB | INT8 quantized thermal | ✅ **YES** |
| `acoustic_anomaly.tflite` | ~3 MB | INT8 quantized acoustic | ✅ **YES** |

**Remember**: Only `.tflite` files go to Pi, NOT datasets or `.h5` files!

---

## 🔍 Troubleshooting Quick Fixes

### Dataset Not Found
```powershell
# Re-extract specific dataset
cd "d:\PREMONITOR\datasets\time-series anomaly detection datasets"
Expand-Archive "secom.zip" -DestinationPath "secom" -Force
```

### Import Errors
```powershell
# Install dependencies
pip install tensorflow librosa pandas tqdm numpy
```

### Out of Memory
```python
# In premonitor_train_models_py.py, reduce batch sizes:
batch_size=16  # Was 32
```

### Low Accuracy
- Increase epochs: `epochs=100` instead of `50`
- Verify dataset labels are correct
- Check validation split is balanced

---

## 📈 Expected Training Times (GPU)

| Model | Stage | Duration | Output |
|-------|-------|----------|--------|
| Thermal | Pre-training (FLIR) | 3 hours | Encoder |
| Thermal | Fine-tuning (AAU) | 1 hour | Classifier |
| Acoustic | Training (MIMII+ESC) | 2 hours | Full model |
| **Total** | **All models** | **~6 hours** | Ready for deployment |

---

## 🍇 Raspberry Pi Deployment Checklist

- [ ] Train models on PC (6 hours)
- [ ] Export to INT8 TFLite (2 minutes)
- [ ] Test inference on PC first
- [ ] Copy `.tflite` files to Pi (NOT datasets!)
- [ ] Copy Python scripts to Pi
- [ ] Install `tflite-runtime` on Pi
- [ ] Run `premonitor_main_hardened.py` on Pi
- [ ] Verify real-time inference works

---

## 📂 File Organization

```
PREMONITOR/
├── datasets/              # 30 GB - STAYS ON PC!
│   ├── datasets audio/
│   ├── thermal camera dataset/
│   └── time-series.../
├── models/                # Training outputs
│   ├── *.h5              # Full models (PC only)
│   └── *.tflite          # Deploy to Pi ✅
├── pythonsoftware/        # Python code
│   ├── premonitor_*.py   # Deploy to Pi ✅
│   ├── train_*.py        # PC only (training)
│   └── dataset_loaders.py # PC only
├── scripts/
│   ├── extract_all_datasets.ps1
│   └── verify_datasets.py
└── docs/
    ├── TRAINING_DEPLOYMENT_GUIDE.md
    ├── DATASET_INVENTORY.md
    └── QUICK_REFERENCE.md (this file)
```

---

## 🚨 Critical Warnings

1. **Never copy datasets to Pi** - They're 30 GB and not needed!
2. **Always use .tflite for Pi** - .h5 models are too slow
3. **Verify datasets before training** - Run `verify_datasets.py` first
4. **Use GPU for training** - CPU training takes 10x longer
5. **Test on PC before Pi** - Ensure models work locally first

---

## 📞 Quick Help

- **Dataset issues**: Check `docs/DATASET_INVENTORY.md`
- **Training issues**: Check `docs/TRAINING_DEPLOYMENT_GUIDE.md`
- **Errors**: Look at `logs/training.log`
- **Verification**: Run `pythonsoftware/verify_datasets.py`

---

## 🎓 Key Concepts

**Self-Supervised Pre-training (SimSiam)**:
- Train on unlabeled data (FLIR 21K images)
- Learn robust thermal features
- No labels needed!

**Transfer Learning (Fine-tuning)**:
- Use pre-trained encoder
- Add classification head
- Train on small labeled dataset (AAU VAP)

**Quantization (INT8)**:
- Convert FP32 → INT8
- 10x smaller, 4x faster
- Perfect for Raspberry Pi

**Sensor Fusion**:
- Combine thermal + acoustic + gas
- Detect anomalies with multiple signals
- Reduce false positives

---

**REMEMBER**: Train on PC → Deploy .tflite to Pi → Monitor lab in real-time! 🔬
