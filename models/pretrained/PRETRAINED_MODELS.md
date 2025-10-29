# Pretrained Model Weights for PREMONITOR

**Last Updated**: 2025-10-29
**Purpose**: Document sources, licenses, and provenance of all pretrained models

---

## Overview

PREMONITOR uses publicly available pretrained weights to bootstrap model training with strong feature extractors. This document provides full traceability for compliance and reproducibility.

---

## 1. Thermal Anomaly Detection

### 1.1 Xception Backbone (ImageNet)
- **Source**: Keras Applications / TensorFlow
- **URL**: https://storage.googleapis.com/tensorflow/keras-applications/xception/xception_weights_tf_dim_ordering_tf_kernels_notop.h5
- **Architecture**: Xception (Extreme Inception)
- **Pretrained On**: ImageNet (1.2M images, 1000 classes)
- **Input Shape**: (224, 224, 3)
- **License**: Apache 2.0
- **Paper**: "Xception: Deep Learning with Depthwise Separable Convolutions" (Chollet, 2017)
- **Use Case**: Backbone for thermal SimSiam encoder
- **File**: `thermal/xception_notop_imagenet.h5`
- **Downloaded**: Automatically via `tf.keras.applications.Xception(weights='imagenet')`

### 1.2 SimSiam Pretrained Encoder (Thermal - Custom)
- **Source**: Local training (Stage 1 pre-training on AAU VAP)
- **Architecture**: Xception + SimSiam projection head
- **Pretrained On**: AAU VAP Trimodal thermal images (11,537 images)
- **Training Method**: Self-supervised learning (SimSiam)
- **Use Case**: Feature extraction for thermal anomaly detection
- **File**: `thermal/thermal_encoder_pretrained.h5`
- **Created By**: `train.py --mode full --model thermal` (Stage 1)

### 1.3 Alternative: FLIR ADAS Thermal Weights (Optional)
- **Source**: FLIR Thermal Dataset for ADAS
- **URL**: https://www.flir.com/oem/adas/adas-dataset-form/ (Registration required)
- **Status**: Not automatically downloaded (requires manual registration)
- **License**: FLIR ADAS Dataset License (Academic/Research use)
- **Use Case**: Fine-tuning for electronics/machinery thermal signatures
- **Note**: Due to license restrictions, not included in automated download

---

## 2. Acoustic Anomaly Detection

### 2.1 YAMNet (AudioSet)
- **Source**: TensorFlow Hub
- **URL**: https://tfhub.dev/google/yamnet/1
- **Architecture**: MobileNet-based audio classification
- **Pretrained On**: AudioSet (2M+ audio clips, 521 classes)
- **Input**: 16kHz mono audio, mel-spectrograms (64 bins)
- **License**: Apache 2.0
- **Paper**: "Multi-task Self-supervised Learning for Robust Speech Recognition" (Google, 2020)
- **Use Case**: Audio feature extraction for anomaly detection
- **File**: `acoustic/yamnet/`
- **Download Command**: See `download_pretrained_weights.py`

### 2.2 PANNs CNN14 (AudioSet)
- **Source**: PANNs (Pretrained Audio Neural Networks)
- **URL**: https://zenodo.org/record/3987831
- **Architecture**: CNN14 (14-layer convolutional network)
- **Pretrained On**: AudioSet (527 classes)
- **Input**: 32kHz mono audio, log-mel spectrograms
- **License**: MIT License
- **Paper**: "PANNs: Large-Scale Pretrained Audio Neural Networks for Audio Pattern Recognition" (Kong et al., 2020)
- **Zenodo DOI**: 10.5281/zenodo.3987831
- **File**: `acoustic/panns_cnn14.pth` (PyTorch) → convert to TF
- **Status**: Optional enhancement (not required for MVP)

### 2.3 MIMII Baseline CNN (Custom)
- **Source**: Local training on MIMII dataset
- **Architecture**: Simple CNN for spectrogram classification
- **Pretrained On**: MIMII 0_dB_fan dataset (normal/abnormal machine sounds)
- **Use Case**: Machine sound anomaly detection baseline
- **File**: `acoustic/mimii_baseline_cnn.h5`
- **Created By**: `train.py --mode full --model acoustic`
- **Status**: Requires MIMII dataset download (10.4 GB)

---

## 3. Time-Series Anomaly Detection (Optional)

### 3.1 LSTM Autoencoder (Generic)
- **Source**: Custom implementation (Reis & Serôdio architecture)
- **Architecture**: LSTM Encoder-Decoder (32-16-16-32 units)
- **Pretrained On**: Synthetic or NASA bearing dataset
- **Use Case**: Gas sensor / vibration anomaly detection
- **File**: `timeseries/lstm_autoencoder.h5`
- **Status**: To be trained on domain-specific data
- **Alternative**: Use pre-trained autoencoder from TensorFlow Model Garden

---

## 4. Download Instructions

### Automatic Download (Recommended)

```bash
python scripts/download_pretrained_weights.py --all
```

### Manual Download Steps

#### YAMNet (TensorFlow Hub)
```python
import tensorflow_hub as hub
model = hub.load('https://tfhub.dev/google/yamnet/1')
# Model will be cached in ~/.cache/tfhub_modules/
```

#### PANNs CNN14 (Optional)
```bash
# Download from Zenodo
wget https://zenodo.org/record/3987831/files/Cnn14_mAP%3D0.431.pth -O models/pretrained/acoustic/panns_cnn14.pth

# Convert PyTorch to TensorFlow (requires pytorch2keras or ONNX)
python scripts/convert_pytorch_to_tf.py --model panns_cnn14
```

#### Xception (Automatic via Keras)
```python
from tensorflow.keras.applications import Xception
model = Xception(weights='imagenet', include_top=False)
# Weights automatically downloaded to ~/.keras/models/
```

---

## 5. Model Conversion Pipeline

### PyTorch → TensorFlow
1. **Export to ONNX**:
   ```python
   torch.onnx.export(pytorch_model, dummy_input, "model.onnx")
   ```

2. **Convert ONNX to TensorFlow**:
   ```bash
   pip install onnx-tf
   onnx-tf convert -i model.onnx -o model_tf
   ```

3. **Save as Keras H5**:
   ```python
   tf.keras.models.save_model(model, "model.h5")
   ```

### TensorFlow Hub → Local H5
```python
import tensorflow_hub as hub
model = hub.load('https://tfhub.dev/...')
# Extract and save as Keras model
```

---

## 6. Licensing Summary

| Model | License | Commercial Use | Attribution Required |
|-------|---------|----------------|---------------------|
| Xception (ImageNet) | Apache 2.0 | ✓ Yes | ✓ Yes |
| YAMNet | Apache 2.0 | ✓ Yes | ✓ Yes |
| PANNs CNN14 | MIT | ✓ Yes | ✓ Yes |
| FLIR ADAS | Custom | ❌ Research Only | ✓ Yes |
| MIMII Dataset | CC BY 4.0 | ✓ Yes | ✓ Yes |
| AAU VAP | Academic | ⚠ Check | ✓ Yes |

**Compliance Note**: PREMONITOR project is released under MIT License. All pretrained models used are compatible with academic/research use. For commercial deployment, verify FLIR ADAS and AAU VAP licensing terms.

---

## 7. References

1. **Xception**: Chollet, F. (2017). "Xception: Deep Learning with Depthwise Separable Convolutions." CVPR.
2. **YAMNet**: Plakal, M., & Ellis, D. (2020). "YAMNet." TensorFlow Hub.
3. **PANNs**: Kong, Q., et al. (2020). "PANNs: Large-Scale Pretrained Audio Neural Networks." IEEE/ACM TASLP.
4. **SimSiam**: Chen, X., & He, K. (2021). "Exploring Simple Siamese Representation Learning." CVPR.
5. **MIMII**: Purohit, H., et al. (2019). "MIMII Dataset: Sound Dataset for Malfunctioning Industrial Machine Investigation." DCASE Workshop.

---

## 8. File Structure

```
models/pretrained/
├── PRETRAINED_MODELS.md          # This file
├── thermal/
│   ├── xception_notop_imagenet.h5
│   ├── thermal_encoder_pretrained.h5
│   └── metadata.json
├── acoustic/
│   ├── yamnet/                   # TensorFlow Hub cache
│   ├── mimii_baseline_cnn.h5
│   ├── panns_cnn14.pth          # Optional
│   └── metadata.json
└── timeseries/
    ├── lstm_autoencoder.h5
    └── metadata.json
```

---

## 9. Verification

After downloading, verify integrity:

```bash
python scripts/verify_pretrained_models.py
```

Expected output:
- ✓ Xception weights loaded successfully
- ✓ YAMNet loaded from TensorFlow Hub
- ✓ Model input/output shapes verified
- ✓ Inference smoke test passed

---

**For questions or issues, see `TRAINING_AND_DEPLOYMENT_GUIDE.md`**
