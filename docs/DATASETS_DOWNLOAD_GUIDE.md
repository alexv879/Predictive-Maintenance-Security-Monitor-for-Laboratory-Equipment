# PREMONITOR Dataset Download Guide

**Important:** Datasets are NOT included in this repository due to size (~1.2 TB total). You must download them separately before training models.

---

## Required Datasets (8 Total)

### 1. FLIR ADAS v2 Dataset (21,488 thermal images, ~20 GB)
**Purpose:** Pretrain thermal CNN on general thermal patterns  
**Download:** https://www.flir.com/oem/adas/adas-dataset-form/  
**License:** Free for research with registration  
**Extract to:** `datasets/flir_adas_v2/`

**Instructions:**
1. Register at FLIR website and request download link
2. Download `FLIR_ADAS_v2.tar.gz`
3. Extract: `tar -xzf FLIR_ADAS_v2.tar.gz -C datasets/flir_adas_v2/`

---

### 2. AAU VAP Trimodal Dataset (14,000+ labeled thermal images, ~50 GB)
**Purpose:** Fine-tune thermal CNN on labeled thermal data  
**Download:** https://www.vap.aau.dk/rgb-t-d/  
**License:** Free for academic research  
**Extract to:** `datasets/thermal camera dataset/trimodaldataset/`

**Instructions:**
1. Download from AAU VAP website
2. Extract: Place in `datasets/thermal camera dataset/trimodaldataset/TrimodalDataset/`
3. Verify structure: Should have `Scene 1/`, `Scene 2/`, `Scene 3/` folders

---

### 3. MIMII Dataset (1,418 industrial fan sounds, ~5 GB)
**Purpose:** Train acoustic CNN on motor/compressor sounds  
**Download:** https://zenodo.org/record/3384388  
**License:** Creative Commons Attribution 4.0  
**Extract to:** `datasets/datasets audio/Mimii/`

**Instructions:**
1. Download from Zenodo: `MIMII_fan_0dB.zip`
2. Extract: `unzip MIMII_fan_0dB.zip -d "datasets/datasets audio/Mimii/"`
3. Verify structure: Should have `0_dB_fan/fan/id_00/`, `id_02/`, etc.

---

### 4. NASA Turbofan Engine Degradation (C-MAPSS, ~100 MB)
**Purpose:** Train LSTM Autoencoder for predictive maintenance  
**Download:** https://ti.arc.nasa.gov/tech/dash/groups/pcoe/prognostic-data-repository/#turbofan  
**License:** Public domain (NASA)  
**Extract to:** `datasets/time-series anomaly detection datasets/`

**Instructions:**
1. Download `CMAPSSData.zip` from NASA Prognostics Data Repository
2. Extract: `unzip CMAPSSData.zip -d "datasets/time-series anomaly detection datasets/"`
3. Files: `train_FD001.txt`, `test_FD001.txt`, etc.

---

### 5. ESC-50 Environmental Sound Classification (2,000 sounds, ~600 MB)
**Purpose:** Augment acoustic training with diverse environmental sounds  
**Download:** https://github.com/karolpiczak/ESC-50  
**License:** Creative Commons Attribution Non-Commercial  
**Extract to:** `datasets/datasets audio/ESC-50-master/`

**Instructions:**
1. Clone or download: `git clone https://github.com/karolpiczak/ESC-50.git`
2. Move to: `datasets/datasets audio/ESC-50-master/ESC-50-master/`
3. Verify: Should have `audio/` and `meta/esc50.csv`

---

### 6. UrbanSound8K (8,732 urban sounds, ~6 GB)
**Purpose:** Further acoustic model training  
**Download:** https://urbansounddataset.weebly.com/urbansound8k.html  
**License:** Creative Commons Attribution Non-Commercial  
**Extract to:** `datasets/datasets audio/urbansound8kdataset/`

**Instructions:**
1. Register and download from UrbanSound8K website
2. Extract: `tar -xzf UrbanSound8K.tar.gz -C "datasets/datasets audio/urbansound8kdataset/"`
3. Verify: Should have `fold1/` through `fold10/` and `UrbanSound8K.csv`

---

### 7. SECOM Semiconductor Manufacturing (Optional, ~10 MB)
**Purpose:** Future expansion to manufacturing equipment  
**Download:** https://archive.ics.uci.edu/ml/datasets/SECOM  
**License:** Creative Commons Attribution 4.0  
**Extract to:** `datasets/time-series anomaly detection datasets/secom/`

**Instructions:**
1. Download `secom.data` and `secom_labels.data`
2. Place in: `datasets/time-series anomaly detection datasets/secom/`

---

### 8. CASAS Smart Home Activity (Optional, ~50 MB)
**Purpose:** Human activity pattern recognition (future)  
**Download:** http://casas.wsu.edu/datasets/  
**License:** Contact WSU for academic use  
**Extract to:** `datasets/time-series anomaly detection datasets/casas/`

---

## Quick Setup Commands

### Windows PowerShell
```powershell
# Create dataset directories
New-Item -ItemType Directory -Force -Path "datasets/flir_adas_v2"
New-Item -ItemType Directory -Force -Path "datasets/thermal camera dataset/trimodaldataset"
New-Item -ItemType Directory -Force -Path "datasets/datasets audio/Mimii"
New-Item -ItemType Directory -Force -Path "datasets/datasets audio/ESC-50-master"
New-Item -ItemType Directory -Force -Path "datasets/datasets audio/urbansound8kdataset"
New-Item -ItemType Directory -Force -Path "datasets/time-series anomaly detection datasets"

# After downloading, extract using 7-Zip or built-in tools
```

### Linux/Mac
```bash
# Create dataset directories
mkdir -p datasets/flir_adas_v2
mkdir -p "datasets/thermal camera dataset/trimodaldataset"
mkdir -p "datasets/datasets audio/Mimii"
mkdir -p "datasets/datasets audio/ESC-50-master"
mkdir -p "datasets/datasets audio/urbansound8kdataset"
mkdir -p "datasets/time-series anomaly detection datasets"

# Extract example (adjust paths)
tar -xzf FLIR_ADAS_v2.tar.gz -C datasets/flir_adas_v2/
unzip MIMII_fan_0dB.zip -d "datasets/datasets audio/Mimii/"
```

---

## Verify Dataset Installation

After downloading and extracting, run:

```powershell
# Check that datasets are in place
python scripts/check_datasets.py

# Or run dataset tests
python tests/test_datasets.py
```

Expected output:
```
[OK] ESC-50 metadata found
[OK] UrbanSound8K metadata found
[OK] Trimodal dataset directory found
Results: 3/3 tests passed
```

---

## Disk Space Requirements

| Dataset | Size | Required |
|---------|------|----------|
| FLIR ADAS v2 | ~20 GB | Yes |
| AAU VAP Trimodal | ~50 GB | Yes |
| MIMII | ~5 GB | Yes |
| NASA Turbofan | ~100 MB | Yes |
| ESC-50 | ~600 MB | Yes |
| UrbanSound8K | ~6 GB | Yes |
| SECOM | ~10 MB | Optional |
| CASAS | ~50 MB | Optional |
| **Total (required)** | **~82 GB** | - |
| **Total (all)** | **~82.2 GB** | - |

**Note:** Extracted datasets will be larger due to decompression.

---

## License Compliance

**Important:** Each dataset has its own license terms. You are responsible for:
1. Registering with dataset providers where required
2. Citing datasets in publications
3. Complying with non-commercial/academic-only restrictions
4. Not redistributing datasets without permission

See individual dataset websites for full license terms.

---

## Troubleshooting

### Dataset tests fail in CI
- Datasets are intentionally excluded from Git (see `.gitignore`)
- CI workflow skips dataset tests by default
- Download datasets locally before running training

### Extraction errors
- Use 7-Zip on Windows or `tar`/`unzip` on Linux/Mac
- Ensure you have enough disk space (~100 GB free)
- Check file integrity with MD5/SHA checksums if provided

### Missing metadata files
- Verify extraction path matches expected structure
- Some datasets require specific folder naming (e.g., `ESC-50-master/ESC-50-master/`)
- Re-extract if structure is incorrect

---

## Training Without Full Datasets (Smoke Test)

For quick testing without downloading all datasets:

```powershell
# Run smoke test with minimal synthetic data
python train.py --mode smoke_test --model all
```

This uses small generated samples for CI/testing purposes.

---

## Contact

For dataset access issues:
- FLIR: Contact FLIR support
- AAU VAP: Email vap@aau.dk
- MIMII: Use Zenodo DOI link
- NASA: Public domain, no registration
- ESC-50: GitHub repo
- UrbanSound8K: Request via website form

For PREMONITOR project questions:
- Repository owner: Alexandru Emanuel Vasile
- See `LICENSE` for usage terms

---

**Last Updated:** 2025-10-29
