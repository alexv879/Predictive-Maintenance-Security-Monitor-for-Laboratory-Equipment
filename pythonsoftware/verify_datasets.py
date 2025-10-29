# -*- coding: utf-8 -*-
"""
Premonitor: verify_datasets.py

Quick verification script to check that all datasets are accessible and properly extracted.
Run this BEFORE starting training to ensure everything is ready.
"""

import os
import sys
from pathlib import Path

def check_path(path, description, required=True):
    """Check if a path exists and report status."""
    exists = os.path.exists(path)
    status = "✓" if exists else "✗"
    color = "\033[92m" if exists else "\033[91m"  # Green if exists, Red if not
    reset = "\033[0m"
    
    print(f"{color}{status}{reset} {description}")
    print(f"   Path: {path}")
    
    if not exists and required:
        print(f"   {color}REQUIRED - Please extract or verify this dataset!{reset}")
    
    return exists

def count_files(directory, extensions):
    """Count files with specific extensions in a directory."""
    count = 0
    if os.path.exists(directory):
        for ext in extensions:
            count += len(list(Path(directory).rglob(f'*{ext}')))
    return count

def main():
    print("=" * 80)
    print(" " * 20 + "PREMONITOR DATASET VERIFICATION")
    print("=" * 80)
    print()
    
    base_path = Path("d:/PREMONITOR/datasets")
    results = {}
    
    # ========================================================================
    # AUDIO DATASETS
    # ========================================================================
    print("### AUDIO DATASETS ###\n")
    
    # MIMII Dataset
    print("1. MIMII (Industrial Fan Sounds)")
    mimii_path = base_path / "datasets audio/Mimii/0_dB_fan/fan"
    mimii_ok = check_path(mimii_path, "MIMII Base Directory", required=True)
    if mimii_ok:
        # Count files in each machine ID
        for machine_id in ['id_00', 'id_02', 'id_04', 'id_06']:
            normal_count = count_files(mimii_path / machine_id / 'normal', ['.wav'])
            abnormal_count = count_files(mimii_path / machine_id / 'abnormal', ['.wav'])
            print(f"   {machine_id}: {normal_count} normal, {abnormal_count} abnormal")
    results['mimii'] = mimii_ok
    print()
    
    # ESC-50 Dataset
    print("2. ESC-50 (Environmental Sounds)")
    esc50_path = base_path / "datasets audio/ESC-50-master/ESC-50-master"
    esc50_ok = check_path(esc50_path / "audio", "ESC-50 Audio Directory", required=True)
    esc50_meta_ok = check_path(esc50_path / "meta/esc50.csv", "ESC-50 Metadata", required=True)
    if esc50_ok:
        audio_count = count_files(esc50_path / "audio", ['.wav'])
        print(f"   Found {audio_count} audio files (expected: 2,000)")
    results['esc50'] = esc50_ok and esc50_meta_ok
    print()
    
    # UrbanSound8K Dataset
    print("3. UrbanSound8K (Urban Sounds)")
    urban_path = base_path / "datasets audio/urbansound8kdataset"
    urban_ok = check_path(urban_path, "UrbanSound8K Base Directory", required=True)
    urban_meta_ok = check_path(urban_path / "UrbanSound8K.csv", "UrbanSound8K Metadata", required=True)
    if urban_ok:
        total_audio = 0
        for fold in range(1, 11):
            fold_count = count_files(urban_path / f"fold{fold}", ['.wav'])
            total_audio += fold_count
        print(f"   Found {total_audio} audio files across 10 folds (expected: 8,732)")
    results['urbansound8k'] = urban_ok and urban_meta_ok
    print()
    
    # ========================================================================
    # THERMAL DATASETS
    # ========================================================================
    print("### THERMAL DATASETS ###\n")
    
    # FLIR ADAS v2 Dataset
    print("4. FLIR ADAS v2 (Thermal Pre-training)")
    flir_path = base_path / "thermal camera dataset/FLIR_ADAS_v2"
    flir_train_ok = check_path(flir_path / "images_thermal_train/data", "FLIR Training Images", required=True)
    flir_val_ok = check_path(flir_path / "images_thermal_val/data", "FLIR Validation Images", required=False)
    if flir_train_ok:
        train_count = count_files(flir_path / "images_thermal_train", ['.jpeg', '.jpg'])
        val_count = count_files(flir_path / "images_thermal_val", ['.jpeg', '.jpg'])
        print(f"   Training images: {train_count} (expected: ~21,488)")
        print(f"   Validation images: {val_count}")
    results['flir'] = flir_train_ok
    print()
    
    # AAU VAP Trimodal Dataset
    print("5. AAU VAP Trimodal (Labeled Thermal)")
    aau_path = base_path / "thermal camera dataset/trimodaldataset/TrimodalDataset"
    aau_ok = check_path(aau_path, "AAU VAP Base Directory", required=True)
    if aau_ok:
        for scene in ['Scene 1', 'Scene 2', 'Scene 3']:
            scene_path = aau_path / scene
            thermal_count = count_files(scene_path / "SyncT", ['.png'])
            anno_exists = os.path.exists(scene_path / "annotations.csv")
            print(f"   {scene}: {thermal_count} thermal images, annotations: {'✓' if anno_exists else '✗'}")
    results['aau_vap'] = aau_ok
    print()
    
    # ========================================================================
    # TIME-SERIES DATASETS
    # ========================================================================
    print("### TIME-SERIES DATASETS ###\n")
    
    # Turbofan Dataset
    print("6. Turbofan Engine Degradation (LSTM-AE Training)")
    turbofan_path = base_path / "time-series anomaly detection datasets/17.+Turbofan+Engine+Degradation+Simulation+Data+Set+2/17. Turbofan Engine Degradation Simulation Data Set 2"
    turbofan_ok = True
    for dataset_id in ['FD001', 'FD002', 'FD003', 'FD004']:
        train_file = turbofan_path / f"train_{dataset_id}.txt"
        exists = check_path(train_file, f"Turbofan {dataset_id}", required=(dataset_id == 'FD001'))
        turbofan_ok = turbofan_ok and exists if dataset_id == 'FD001' else turbofan_ok
    results['turbofan'] = turbofan_ok
    print()
    
    # SECOM Dataset
    print("7. SECOM (Semiconductor Manufacturing)")
    secom_path = base_path / "time-series anomaly detection datasets/secom"
    secom_data_ok = check_path(secom_path / "secom.data", "SECOM Data File", required=False)
    secom_labels_ok = check_path(secom_path / "secom_labels.data", "SECOM Labels File", required=False)
    results['secom'] = secom_data_ok and secom_labels_ok
    print()
    
    # CASAS Aruba Dataset
    print("8. CASAS Aruba (Smart Home Activity)")
    casas_path = base_path / "time-series anomaly detection datasets/CASAS aruba dataset"
    casas_ok = check_path(casas_path / "data/data", "CASAS Data Directory", required=False)
    if casas_ok:
        csv_count = count_files(casas_path / "data/data", ['.csv'])
        print(f"   Found {csv_count} CSV files")
    results['casas'] = casas_ok
    print()
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("=" * 80)
    print(" " * 30 + "SUMMARY")
    print("=" * 80)
    print()
    
    ready_count = sum(results.values())
    total_count = len(results)
    
    print(f"Datasets Ready: {ready_count}/{total_count}\n")
    
    # Critical datasets for PREMONITOR
    critical = ['mimii', 'flir', 'esc50']
    critical_ok = all(results.get(ds, False) for ds in critical)
    
    if critical_ok:
        print("✓ \033[92mALL CRITICAL DATASETS READY!\033[0m")
        print("  You can start training immediately with:")
        print("    - Thermal Model: python premonitor_train_models_py.py --model thermal")
        print("    - Acoustic Model: python premonitor_train_models_py.py --model acoustic")
    else:
        print("✗ \033[91mCRITICAL DATASETS MISSING!\033[0m")
        print("  Required for PREMONITOR to work:")
        for ds in critical:
            status = "✓" if results.get(ds, False) else "✗ MISSING"
            print(f"    {status} {ds.upper()}")
    
    print()
    
    # Optional datasets
    optional = ['urbansound8k', 'aau_vap', 'turbofan', 'secom', 'casas']
    optional_missing = [ds for ds in optional if not results.get(ds, False)]
    
    if optional_missing:
        print("Optional datasets (not critical, but recommended):")
        for ds in optional_missing:
            print(f"  ⚠ {ds.upper()} - Not found or needs extraction")
    
    print()
    print("=" * 80)
    
    return 0 if critical_ok else 1

if __name__ == "__main__":
    sys.exit(main())
