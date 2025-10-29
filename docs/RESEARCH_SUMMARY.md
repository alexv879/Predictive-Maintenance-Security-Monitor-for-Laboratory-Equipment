# PREMONITOR - Research Papers and Documentation Summary

**Date**: 2025-10-29
**Purpose**: Map research findings to implementation decisions

---

## Documents Reviewed

### 1. Project Plan (`plan.txt`)

**Key Points**:
- **Phased Development**: No-budget MVP using public datasets as mock sensor inputs
- **Two-Stage Thermal Model Training**:
  - Stage 1: Fine-tune XceptionNet on AAU VAP dataset (general thermal properties)
  - Stage 2: Further fine-tune on FLIR dataset (machine/electronic heat signatures)
- **Two-Stage Acoustic Model Training**:
  - Stage 1: Train GhostNetV2 backbone on MIMII/DCASE (core machine sounds)
  - Stage 2: Fine-tune with UrbanSound8K + ESC-50 (environmental robustness, reduce false positives)
- **Time-Series Approach**: LSTM Autoencoder (Reis & Serôdio paper validation)
- **Mock Hardware Testing**: Create mock_hardware.py to simulate sensors using dataset samples

**Implementation Mapping**:
- ✓ Use SimSiam self-supervised pre-training with XceptionNet backbone
- ✓ Multi-stage fine-tuning pipeline for thermal models
- ✓ Acoustic model: Train on MIMII, fine-tune on environmental sounds
- ✓ Mock hardware module already exists in pythonsoftware/
- ⚠ GhostNetV2 not implemented (use simple CNN for MVP, upgrade later)

---

### 2. MIMII Dataset README (`mimmii dataset readme.txt`)

**Key Points**:
- **Dataset**: Sound dataset for malfunctioning industrial machine investigation
- **Contents**: 4 machine types (valves, pumps, fans, slide rails), 7 models each
- **Normal Sounds**: 5000-10000 seconds per model
- **Anomalous Sounds**: ~1000 seconds per model (contamination, leakage, unbalance, rail damage)
- **Background Noise**: Mixed real factory noise at -6dB, 0dB, 6dB levels
- **Recommendation**: Start with `0_dB_fan.zip` (10.4 GB) - cleanest baseline data
- **Sampling**: 16 kHz, 16-bit, 8-channel microphone array

**Implementation Mapping**:
- ✓ Use 0_dB level for initial training (normal baseline noise)
- ✓ Train on `train/normal` folder for baseline model
- ✓ Test on `test/normal` and `test/abnormal` for validation
- ✓ Sample rate: 16kHz for acoustic model input
- ⚠ Full dataset not downloaded - create small-sample training mode

---

### 3. ESC-50 Dataset README

**Key Points**:
- **Dataset**: 2000 environmental audio recordings, 5-second clips
- **Classes**: 50 semantic classes, 40 examples each
- **Categories**: Animals, Natural soundscapes, Human non-speech, Interior/domestic, Exterior/urban
- **Purpose**: Environmental sound classification benchmark
- **Pre-arranged Folds**: 5-fold cross-validation structure
- **Human Accuracy Baseline**: 81.3%
- **State-of-Art**: 98.25% (HTSAT-22 with natural language supervision)

**Implementation Mapping**:
- ✓ Use ESC-50 for acoustic model fine-tuning (environmental robustness)
- ✓ Use as negative examples to reduce false positives (label as "ignore" class)
- ✓ 5-fold structure useful for validation
- ✓ Target: Distinguish machine anomalies from environmental sounds

---

### 4. AAU VAP Trimodal Dataset (`thermalreadme.txt`)

**Key Points**:
- **Modalities**: Thermal (Axis Q1922), Depth (Kinect V1), RGB (Kinect V1)
- **Scenes**: 3 scenes (Meeting room full depth, Meeting room constrained, Canteen)
- **Thermal Images**: 32-bit bitmap, 680x480 px, radial lens distortion
- **Depth Images**: 16-bit PNG, depth in mm, range 1000-3300mm valid
- **Registration**: Calibration files (calibVars.yml) for modality alignment
- **Use Case**: People segmentation and tracking

**Implementation Mapping**:
- ✓ Use thermal images for Stage 1 pre-training (general thermal properties)
- ✓ Input resolution: Resize to 224x224 for XceptionNet (config.THERMAL_MODEL_INPUT_SHAPE)
- ⚠ Radial distortion present - may affect quality (accept for MVP, rectify in V2)
- ✓ Trimodal data available but using thermal only for anomaly detection

---

### 5. Fine-Tuning Strategy (`finetune.txt`)

**Key Points**:
- **Multi-Stage Thermal Training**:
  1. Load XceptionNet with ImageNet weights
  2. Fine-tune on AAU VAP dataset
  3. Continue fine-tuning on FLIR dataset
- **FLIR Dataset**: For machine/electronic heat signatures
- **Purpose**: Transfer learning from general thermal → specific use case

**Implementation Mapping**:
- ✓ Implemented SimSiam pre-training approach (better than direct fine-tuning)

---

## 6. Pretrained Model Provenance (NEW - Added 2025-10-29)

### 6.1 Thermal Models

**Xception (ImageNet)**:
- **Paper**: Chollet, F. (2017). "Xception: Deep Learning with Depthwise Separable Convolutions." CVPR.
- **Source**: Keras Applications / TensorFlow
- **Weights**: ImageNet (1.2M images, 1000 classes)
- **License**: Apache 2.0 ✓ Commercial use allowed
- **URL**: https://storage.googleapis.com/tensorflow/keras-applications/xception/
- **Use in PREMONITOR**: Backbone for thermal SimSiam encoder

**SimSiam Architecture**:
- **Paper**: Chen, X., & He, K. (2021). "Exploring Simple Siamese Representation Learning." CVPR.
- **Method**: Self-supervised learning without negative pairs
- **Training**: Stage 1 pre-training on AAU VAP thermal images
- **Output**: Pretrained encoder for thermal anomaly detection

**FLIR ADAS Dataset** (Optional):
- **Source**: FLIR Systems - Thermal Dataset for ADAS
- **License**: FLIR ADAS Dataset License (Research/Academic use)
- **Status**: Manual download (requires registration)
- **URL**: https://www.flir.com/oem/adas/adas-dataset-form/
- **Use**: Fine-tuning for electronics/machinery thermal signatures

### 6.2 Acoustic Models

**YAMNet (AudioSet)**:
- **Paper**: Plakal, M., & Ellis, D. (2020). "YAMNet." TensorFlow Hub / Google Research.
- **Source**: TensorFlow Hub
- **Weights**: AudioSet (2M+ audio clips, 521 classes)
- **Architecture**: MobileNet-v1 based audio classification
- **License**: Apache 2.0 ✓ Commercial use allowed
- **URL**: https://tfhub.dev/google/yamnet/1
- **Input**: 16kHz mono audio waveform
- **Output**: 1024-dim embeddings for transfer learning
- **Use in PREMONITOR**: Audio feature extraction for anomaly detection

**PANNs CNN14 (AudioSet)** (Optional):
- **Paper**: Kong, Q., et al. (2020). "PANNs: Large-Scale Pretrained Audio Neural Networks for Audio Pattern Recognition." IEEE/ACM TASLP.
- **Source**: Zenodo (DOI: 10.5281/zenodo.3987831)
- **Weights**: AudioSet (527 classes)
- **Architecture**: 14-layer CNN with attention
- **License**: MIT ✓ Commercial use allowed
- **URL**: https://zenodo.org/record/3987831
- **Format**: PyTorch (.pth) - requires conversion to TensorFlow
- **Use in PREMONITOR**: Advanced acoustic feature extraction (optional enhancement)

**MIMII Dataset**:
- **Paper**: Purohit, H., et al. (2019). "MIMII Dataset: Sound Dataset for Malfunctioning Industrial Machine Investigation." DCASE2020 Challenge.
- **Source**: Zenodo (DOI: 10.5281/zenodo.3384388)
- **License**: CC BY 4.0 ✓ Commercial use allowed with attribution
- **Size**: 10.4 GB (0_dB_fan baseline recommended)
- **Content**: Normal & abnormal machine sounds (fans, pumps, valves, slide rails)
- **Sampling**: 16 kHz, 16-bit, 8-channel microphone array
- **Use in PREMONITOR**: Training acoustic anomaly baseline model

### 6.3 Time-Series Models

**LSTM Autoencoder Architecture**:
- **Paper**: Reis, P., & Serôdio, C. (Various). "LSTM-based Autoencoder for Anomaly Detection in Time-Series."
- **Source**: Custom implementation (template provided)
- **Architecture**: 32-16-16-32 LSTM units, encoder-decoder
- **Training**: Domain-specific (gas sensors, vibration data)
- **License**: MIT (PREMONITOR implementation)
- **Use in PREMONITOR**: Gas sensor / vibration anomaly detection

### 6.4 Licensing Summary

| Model | License | Commercial Use | Attribution Required | Status |
|-------|---------|----------------|---------------------|--------|
| Xception (ImageNet) | Apache 2.0 | ✓ Yes | ✓ Yes | Auto-download |
| YAMNet | Apache 2.0 | ✓ Yes | ✓ Yes | Hub URL |
| PANNs CNN14 | MIT | ✓ Yes | ✓ Yes | Optional |
| FLIR ADAS | Custom | ❌ Research Only | ✓ Yes | Manual |
| MIMII Dataset | CC BY 4.0 | ✓ Yes | ✓ Yes | Manual download |
| SimSiam Encoder | Apache 2.0 | ✓ Yes | ✓ Yes | Local training |

**PREMONITOR License**: MIT - All pretrained models used are compatible with MIT licensing for academic/research deployment. For commercial deployment, verify FLIR ADAS and AAU VAP licensing terms.

### 6.5 Model Performance Baselines

**Xception (ImageNet)**:
- **Top-1 Accuracy**: 79.0% on ImageNet validation
- **Top-5 Accuracy**: 94.5% on ImageNet validation
- **Parameters**: 22.9M
- **Use**: Transfer learning reduces training time by 10-50x

**YAMNet (AudioSet)**:
- **mAP**: 0.495 on AudioSet evaluation
- **Classes**: 521 environmental and machine sounds
- **Latency**: ~5ms per 0.96s audio frame
- **Use**: Strong acoustic feature extractor for fine-tuning

**MIMII Baseline**:
- **AUC**: 0.70-0.95 depending on machine type
- **Best Performance**: Fan anomaly detection (0.95 AUC)
- **Use**: State-of-art baseline for machine sound anomaly detection

**Citations for Attribution**:
```bibtex
@inproceedings{chollet2017xception,
  title={Xception: Deep learning with depthwise separable convolutions},
  author={Chollet, Fran{\c{c}}ois},
  booktitle={CVPR},
  year={2017}
}

@inproceedings{chen2021simsiam,
  title={Exploring simple siamese representation learning},
  author={Chen, Xinlei and He, Kaiming},
  booktitle={CVPR},
  year={2021}
}

@article{kong2020panns,
  title={PANNs: Large-scale pretrained audio neural networks for audio pattern recognition},
  author={Kong, Qiuqiang and others},
  journal={IEEE/ACM TASLP},
  year={2020}
}

@inproceedings{purohit2019mimii,
  title={MIMII dataset: Sound dataset for malfunctioning industrial machine investigation},
  author={Purohit, Harsh and others},
  booktitle={DCASE2020 Workshop},
  year={2019}
}
```
- ✓ Pre-train encoder on unlabeled thermal images (AAU VAP + FLIR)
- ✓ Fine-tune classifier head on labeled normal/anomaly data
- ⚠ FLIR dataset not present locally - use available data only

---

## Research Recommendations Applied to Code

### Thermal Model Pipeline
1. **Architecture**: XceptionNet backbone (proven for image classification)
2. **Pre-training**: SimSiam self-supervised learning on unlabeled thermal images
3. **Input**: 224x224x3 thermal images, normalized to [0,1]
4. **Augmentations**: Random flip, crop, brightness (implemented in utils.py)
5. **Fine-tuning**: Freeze backbone, train classification head on labeled data
6. **Loss**: Negative cosine similarity (pre-training), Binary cross-entropy (fine-tuning)

### Acoustic Model Pipeline
1. **Preprocessing**: Convert audio → log-mel spectrogram
2. **Parameters**:
   - Sample rate: 16kHz (MIMII standard)
   - n_mels: 128
   - Hop length: 512
3. **Input Shape**: 128x128x1 (spectrogram as grayscale image)
4. **Training Strategy**:
   - Normal samples: Label 0
   - Pseudo-anomalies (flipped spectrograms): Label 1
   - Environmental sounds (ESC-50, UrbanSound8K): Label 2 (ignore during loss calc or train as negative class)
5. **Architecture**: Simple CNN (MVP) → GhostNetV2 (V2.0 upgrade)

### Time-Series Model (Future)
1. **Architecture**: LSTM Autoencoder (Reis & Serôdio validation)
2. **Use Case**: Gas sensor, vibration, sequential anomalies
3. **Algorithm**: Isolation Forest for point anomalies (scikit-learn)

### Deployment Optimizations
1. **Quantization**: Post-training INT8 quantization for Raspberry Pi
2. **Runtime**: tflite_runtime (minimal footprint vs full TensorFlow)
3. **Model Size**: Target <10MB per model after quantization
4. **Inference Speed**: <200ms per inference on Pi 4

---

## Datasets Status and Recommendations

| Dataset | Status | Size | Use Case | Priority |
|---------|--------|------|----------|----------|
| ESC-50 | ✓ Present | 2000 files | Environmental sound negative examples | HIGH |
| UrbanSound8K | ✓ Present | 8732 files | Urban noise robustness | HIGH |
| AAU VAP Trimodal | ✓ Present | 11,537 images | Thermal pre-training | HIGH |
| MIMII 0_dB_fan | ⚠ Not present | 10.4 GB | Machine sound anomaly detection | CRITICAL |
| FLIR ADAS | ⚠ Not present | Unknown | Machine/electronic thermal signatures | MEDIUM |

**Recommendations**:
1. **Immediate**: Use ESC-50 + UrbanSound8K for acoustic model training (present)
2. **Immediate**: Use AAU VAP for thermal model pre-training (present)
3. **Required for Full Training**: Download MIMII 0_dB_fan.zip (10.4 GB) - highest priority
4. **Optional Enhancement**: FLIR ADAS dataset for thermal fine-tuning

---

## Training Configuration Recommendations

### Thermal Model
```yaml
pre_training:
  epochs: 50
  batch_size: 32
  learning_rate: 0.001
  optimizer: Adam
  loss: negative_cosine_similarity

fine_tuning:
  epochs: 25
  batch_size: 32
  learning_rate: 0.0001  # Lower for fine-tuning
  optimizer: Adam
  loss: binary_crossentropy
  dropout: 0.5
  freeze_backbone: true (initially)
```

### Acoustic Model
```yaml
training:
  epochs: 30
  batch_size: 64
  learning_rate: 0.001
  optimizer: Adam
  loss: binary_crossentropy

preprocessing:
  sample_rate: 16000
  n_mels: 128
  hop_length: 512
  target_shape: [128, 128, 1]
```

### Quantization
```yaml
export:
  float32: true  # Always export baseline
  dynamic_range: true  # First quantization step
  int8_full: true  # If representative dataset available
  calibration_samples: 100
```

---

## Key Papers Referenced (Available in project)

1. **Self-supervised learning for hotspot detection (thermal)** - SimSiam approach validation
2. **Enhanced Contrastive Ensemble Learning (acoustic)** - Contrastive learning for anomaly detection
3. **EdgeAI for Real-Time Anomaly Detection** - Deployment optimizations for edge devices
4. **Multi-modal sensors fusion based on deep learning** - Sensor fusion strategies
5. **Evolution of Bluetooth/BLE in IoT** - Future connectivity options

---

## Implementation Gaps and TODOs

### Completed
- ✓ Model architecture blueprints (thermal, acoustic, LSTM AE)
- ✓ Data preprocessing utilities (spectrogram, image augmentation)
- ✓ Config management system
- ✓ Mock hardware for testing
- ✓ Alert manager infrastructure

### In Progress
- ⚙ Standalone training script with proper imports
- ⚙ TFLite export and quantization pipeline
- ⚙ Small-sample training mode for smoke tests

### Required
- ❌ Download MIMII dataset (10.4 GB minimum)
- ❌ Create labeled thermal anomaly dataset (normal/anomaly splits)
- ❌ Full training run on complete datasets
- ❌ Raspberry Pi hardware deployment testing

---

**Conclusion**: The research provides clear guidance for a two-stage thermal model (SimSiam pre-training + supervised fine-tuning) and acoustic model (spectrogram CNN with environmental robustness). The mock hardware approach enables software validation without physical sensors. Key blocker is MIMII dataset download for acoustic model training.
