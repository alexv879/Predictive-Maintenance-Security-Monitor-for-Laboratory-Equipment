# PowerShell script to extract all compressed datasets
# Run this script to prepare all datasets for training

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host " " * 20 "PREMONITOR DATASET EXTRACTION" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

$baseDir = "D:\PREMONITOR\datasets"
$extractionLog = @()
$successCount = 0
$skipCount = 0
$failCount = 0

function Extract-Dataset {
    param(
        [string]$ZipPath,
        [string]$DestPath,
        [string]$DatasetName
    )
    
    Write-Host "### $DatasetName ###" -ForegroundColor Yellow
    Write-Host "Source: $ZipPath"
    
    if (-not (Test-Path $ZipPath)) {
        Write-Host "  ✗ ZIP file not found - Skipping" -ForegroundColor Red
        $script:skipCount++
        return $false
    }
    
    # Check if already extracted
    if (Test-Path $DestPath) {
        $fileCount = (Get-ChildItem -Path $DestPath -Recurse -File | Measure-Object).Count
        if ($fileCount -gt 0) {
            Write-Host "  ✓ Already extracted ($fileCount files found) - Skipping" -ForegroundColor Green
            $script:skipCount++
            return $true
        }
    }
    
    Write-Host "  → Extracting..." -ForegroundColor Cyan
    
    try {
        Expand-Archive -Path $ZipPath -DestinationPath $DestPath -Force
        $extractedCount = (Get-ChildItem -Path $DestPath -Recurse -File | Measure-Object).Count
        Write-Host "  ✓ Success! Extracted $extractedCount files" -ForegroundColor Green
        $script:successCount++
        $script:extractionLog += "✓ $DatasetName - $extractedCount files"
        return $true
    }
    catch {
        Write-Host "  ✗ Failed: $_" -ForegroundColor Red
        $script:failCount++
        $script:extractionLog += "✗ $DatasetName - FAILED"
        return $false
    }
    
    Write-Host ""
}

# ============================================================================
# TIME-SERIES DATASETS
# ============================================================================
Write-Host "### TIME-SERIES DATASETS ###" -ForegroundColor Magenta
Write-Host ""

$tsBase = "$baseDir\time-series anomaly detection datasets"

# Turbofan Dataset (nested structure)
$turbofanZip = "$tsBase\17.+Turbofan+Engine+Degradation+Simulation+Data+Set+2.zip"
$turbofanDest = "$tsBase\17.+Turbofan+Engine+Degradation+Simulation+Data+Set+2"
Extract-Dataset -ZipPath $turbofanZip -DestPath $turbofanDest -DatasetName "Turbofan Engine Degradation"

# Check for nested zip inside Turbofan
$turbofanNestedZip = "$turbofanDest\17. Turbofan Engine Degradation Simulation Data Set 2\data_set.zip"
if (Test-Path $turbofanNestedZip) {
    Write-Host "  → Found nested data_set.zip, extracting..." -ForegroundColor Cyan
    $turbofanDataDest = "$turbofanDest\17. Turbofan Engine Degradation Simulation Data Set 2"
    try {
        Expand-Archive -Path $turbofanNestedZip -DestinationPath $turbofanDataDest -Force
        Write-Host "  ✓ Nested archive extracted" -ForegroundColor Green
    }
    catch {
        Write-Host "  ⚠ Nested extraction failed: $_" -ForegroundColor Yellow
    }
}

# SECOM Dataset
$secomZip = "$tsBase\secom.zip"
$secomDest = "$tsBase\secom"
Extract-Dataset -ZipPath $secomZip -DestPath $secomDest -DatasetName "SECOM Semiconductor"

# CASAS Aruba Dataset (with nested archives)
$casasZip = "$tsBase\CASAS aruba dataset.zip"
$casasDest = "$tsBase\CASAS aruba dataset"
$casasExtracted = Extract-Dataset -ZipPath $casasZip -DestPath $casasDest -DatasetName "CASAS Aruba"

if ($casasExtracted) {
    Write-Host "  → Extracting nested CASAS archives..." -ForegroundColor Cyan
    
    # Extract data.zip
    $casasDataZip = "$casasDest\data.zip"
    if (Test-Path $casasDataZip) {
        try {
            Expand-Archive -Path $casasDataZip -DestinationPath "$casasDest\data" -Force
            Write-Host "  ✓ data.zip extracted" -ForegroundColor Green
        }
        catch {
            Write-Host "  ⚠ data.zip extraction failed: $_" -ForegroundColor Yellow
        }
    }
    
    # Extract labeled_data.zip
    $casasLabeledZip = "$casasDest\labeled_data.zip"
    if (Test-Path $casasLabeledZip) {
        try {
            Expand-Archive -Path $casasLabeledZip -DestinationPath "$casasDest\labeled_data" -Force
            Write-Host "  ✓ labeled_data.zip extracted" -ForegroundColor Green
        }
        catch {
            Write-Host "  ⚠ labeled_data.zip extraction failed: $_" -ForegroundColor Yellow
        }
    }
    
    # Extract floorplans.zip
    $casasFloorZip = "$casasDest\floorplans.zip"
    if (Test-Path $casasFloorZip) {
        try {
            Expand-Archive -Path $casasFloorZip -DestinationPath "$casasDest\floorplans" -Force
            Write-Host "  ✓ floorplans.zip extracted" -ForegroundColor Green
        }
        catch {
            Write-Host "  ⚠ floorplans.zip extraction failed: $_" -ForegroundColor Yellow
        }
    }
}

Write-Host ""

# ============================================================================
# THERMAL DATASETS
# ============================================================================
Write-Host "### THERMAL DATASETS ###" -ForegroundColor Magenta
Write-Host ""

$thermalBase = "$baseDir\thermal camera dataset"

# FLIR ADAS v2 (if compressed)
$flirZip = "$thermalBase\FLIR_ADAS_v2.zip"
$flirDest = "$thermalBase\FLIR_ADAS_v2"
if (Test-Path $flirZip) {
    Extract-Dataset -ZipPath $flirZip -DestPath $flirDest -DatasetName "FLIR ADAS v2"
}
else {
    Write-Host "### FLIR ADAS v2 ###" -ForegroundColor Yellow
    if (Test-Path "$flirDest\images_thermal_train") {
        Write-Host "  ✓ Already extracted (not in ZIP format)" -ForegroundColor Green
        $skipCount++
    }
    else {
        Write-Host "  ⚠ Not found - Please verify dataset location" -ForegroundColor Yellow
    }
    Write-Host ""
}

# AAU VAP Trimodal
$aauZip = "$thermalBase\trimodaldatasetzip.zip"
$aauDest = "$thermalBase\trimodaldataset"
if (Test-Path $aauZip) {
    Extract-Dataset -ZipPath $aauZip -DestPath $aauDest -DatasetName "AAU VAP Trimodal"
}
else {
    Write-Host "### AAU VAP Trimodal ###" -ForegroundColor Yellow
    if (Test-Path "$aauDest\TrimodalDataset") {
        Write-Host "  ✓ Already extracted (not in ZIP format)" -ForegroundColor Green
        $skipCount++
    }
    else {
        Write-Host "  ⚠ Not found - Please verify dataset location" -ForegroundColor Yellow
    }
    Write-Host ""
}

# ============================================================================
# AUDIO DATASETS
# ============================================================================
Write-Host "### AUDIO DATASETS ###" -ForegroundColor Magenta
Write-Host ""

$audioBase = "$baseDir\datasets audio"

# UrbanSound8K
$urbanZip = "$audioBase\urbansound8kdataset.zip"
$urbanDest = "$audioBase\urbansound8kdataset"
if (Test-Path $urbanZip) {
    Extract-Dataset -ZipPath $urbanZip -DestPath $urbanDest -DatasetName "UrbanSound8K"
}
else {
    Write-Host "### UrbanSound8K ###" -ForegroundColor Yellow
    if (Test-Path "$urbanDest\fold1") {
        Write-Host "  ✓ Already extracted (not in ZIP format)" -ForegroundColor Green
        $skipCount++
    }
    else {
        Write-Host "  ⚠ Not found - Please verify dataset location" -ForegroundColor Yellow
    }
    Write-Host ""
}

# ESC-50 and MIMII are assumed to be already extracted

# ============================================================================
# SUMMARY
# ============================================================================
Write-Host ""
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host " " * 30 "EXTRACTION SUMMARY" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

Write-Host "Results:" -ForegroundColor White
Write-Host "  ✓ Successfully Extracted: $successCount" -ForegroundColor Green
Write-Host "  → Already Extracted (Skipped): $skipCount" -ForegroundColor Yellow
Write-Host "  ✗ Failed: $failCount" -ForegroundColor Red
Write-Host ""

if ($extractionLog.Count -gt 0) {
    Write-Host "Detailed Log:" -ForegroundColor White
    foreach ($entry in $extractionLog) {
        if ($entry -like "*✓*") {
            Write-Host "  $entry" -ForegroundColor Green
        }
        else {
            Write-Host "  $entry" -ForegroundColor Red
        }
    }
    Write-Host ""
}

# Run verification script
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "Running dataset verification..." -ForegroundColor Cyan
Write-Host ""

if (Test-Path "$PSScriptRoot\verify_datasets.py") {
    try {
        python "$PSScriptRoot\verify_datasets.py"
    }
    catch {
        Write-Host "⚠ Could not run verification script. Run manually:" -ForegroundColor Yellow
        Write-Host "   python pythonsoftware\verify_datasets.py" -ForegroundColor Yellow
    }
}
else {
    Write-Host "⚠ Verification script not found at: $PSScriptRoot\verify_datasets.py" -ForegroundColor Yellow
    Write-Host "  You can verify datasets manually with:" -ForegroundColor Yellow
    Write-Host "    python pythonsoftware\verify_datasets.py" -ForegroundColor White
}

Write-Host ""
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "Extraction complete! You can now run training scripts." -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Cyan
