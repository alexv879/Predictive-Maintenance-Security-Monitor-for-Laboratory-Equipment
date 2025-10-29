# PREMONITOR Dataset Integration Guide

**Purpose**: Step-by-step guide to integrate real datasets into training pipeline  
**Status**: Datasets ready, code integration needed  
**Priority**: HIGH - Replace synthetic data with real datasets

---

## 🎯 Your Datasets Are PERFECT for PREMONITOR

You have exactly what you need for lab safety monitoring:

| Requirement | Dataset | Status | Samples |
|-------------|---------|--------|---------|
| **Fridge failure sounds** | MIMII (fan anomalies) | ✅ Ready | 1,418+ |
| **Fire/temperature** | FLIR ADAS v2 (thermal) | ✅ Ready | 21,488 |
| **Environmental sounds** | ESC-50 | ✅ Ready | 2,000 |
| **Equipment degradation** | Turbofan | ⚠️ Need extract | Unknown |
| **Multi-sensor patterns** | AAU VAP Trimodal | ✅ Ready | 14,000+ |

---

## 📋 Integration Roadmap

### Phase 1: Immediate (< 2 hours)
1. Extract remaining datasets (CASAS, SECOM, Turbofan)
2. Create dataset loader scripts
3. Update `training_config.yaml` with real paths
4. Test loading one batch from each dataset

### Phase 2: Training (4-8 hours GPU)
5. Train thermal model on FLIR ADAS v2
6. Train acoustic model on MIMII
7. Train LSTM-AE on Turbofan
8. Export to INT8 TFLite

### Phase 3: Validation (1 hour)
9. Test with real sensor data or mock data
10. Verify thresholds work correctly
11. Deploy to Raspberry Pi

---

## 🚀 Step 1: Extract Time-Series Datasets

<function_calls>
<invoke name="create_file">
<parameter name="content"># Extract remaining datasets
$baseDir = "D:\PREMONITOR\datasets\time-series anomaly detection datasets"
cd $baseDir

Write-Host "Extracting CASAS Aruba dataset..." -ForegroundColor Green
Expand-Archive -Path "CASAS aruba dataset.zip" -DestinationPath "CASAS_aruba" -Force
Write-Host "✓ CASAS extracted" -ForegroundColor Green

Write-Host "Extracting SECOM dataset..." -ForegroundColor Green
Expand-Archive -Path "secom.zip" -DestinationPath "SECOM" -Force
Write-Host "✓ SECOM extracted" -ForegroundColor Green

Write-Host "Extracting Turbofan dataset..." -ForegroundColor Green
Expand-Archive -Path "17.+Turbofan+Engine+Degradation+Simulation+Data+Set+2.zip" -DestinationPath "Turbofan" -Force
Write-Host "✓ Turbofan extracted" -ForegroundColor Green

Write-Host "`nAll datasets extracted successfully!" -ForegroundColor Cyan
Write-Host "Location: $baseDir" -ForegroundColor Yellow
