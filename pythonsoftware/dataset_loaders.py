# -*- coding: utf-8 -*-
"""
Premonitor: dataset_loaders.py

Comprehensive dataset loading system that integrates ALL available datasets:
- Audio: MIMII, ESC-50, UrbanSound8K
- Thermal: FLIR ADAS v2, AAU VAP Trimodal
- Time-Series: CASAS Aruba, SECOM, Turbofan

This module provides unified data loaders for training on your development PC.
After training, only the learned weights (.tflite files) are deployed to Raspberry Pi.
"""

import os
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers
import librosa
from tqdm import tqdm
import glob
import pandas as pd
import json
from pathlib import Path

# Import our custom project configuration
import config


# ============================================================================
# AUDIO DATASET LOADERS
# ============================================================================

class MIMIIDatasetLoader:
    """
    Loads MIMII dataset (industrial fan sounds with normal/abnormal labels).
    Perfect for lab equipment monitoring (fridge compressor sounds).
    
    Dataset structure:
    - datasets/datasets audio/Mimii/0_dB_fan/fan/
        - id_00/normal/*.wav
        - id_00/abnormal/*.wav
        - id_02/normal/*.wav
        - id_02/abnormal/*.wav
        ... (4 machine IDs total)
    """
    
    def __init__(self, base_path='d:/PREMONITOR/datasets/datasets audio/Mimii/0_dB_fan/fan'):
        self.base_path = base_path
        self.machine_ids = ['id_00', 'id_02', 'id_04', 'id_06']
        
    def load_all_machine_sounds(self, use_all_ids=True):
        """
        Load all normal and abnormal machine sounds.
        
        Args:
            use_all_ids: If True, load from all 4 machine IDs. 
                        If False, use id_00 for train, others for test.
        
        Returns:
            spectrograms: np.array of shape (N, H, W, 1)
            labels: np.array of shape (N,) with 0=normal, 1=abnormal
        """
        print("=" * 60)
        print("LOADING MIMII DATASET (Industrial Fan Sounds)")
        print("=" * 60)
        
        spectrograms = []
        labels = []
        
        ids_to_use = self.machine_ids if use_all_ids else ['id_00']
        
        for machine_id in ids_to_use:
            # Load normal sounds
            normal_dir = os.path.join(self.base_path, machine_id, 'normal')
            if os.path.exists(normal_dir):
                normal_files = glob.glob(os.path.join(normal_dir, '*.wav'))
                print(f"Loading {len(normal_files)} normal sounds from {machine_id}...")
                
                for audio_file in tqdm(normal_files, desc=f"{machine_id}/normal"):
                    spec = self._audio_to_spectrogram(audio_file)
                    if spec is not None:
                        spectrograms.append(spec)
                        labels.append(0)  # Normal
            
            # Load abnormal sounds
            abnormal_dir = os.path.join(self.base_path, machine_id, 'abnormal')
            if os.path.exists(abnormal_dir):
                abnormal_files = glob.glob(os.path.join(abnormal_dir, '*.wav'))
                print(f"Loading {len(abnormal_files)} abnormal sounds from {machine_id}...")
                
                for audio_file in tqdm(abnormal_files, desc=f"{machine_id}/abnormal"):
                    spec = self._audio_to_spectrogram(audio_file)
                    if spec is not None:
                        spectrograms.append(spec)
                        labels.append(1)  # Abnormal
        
        print(f"\nTotal samples loaded: {len(spectrograms)}")
        print(f"  - Normal: {np.sum(np.array(labels) == 0)}")
        print(f"  - Abnormal: {np.sum(np.array(labels) == 1)}")
        
        return np.array(spectrograms), np.array(labels)
    
    def _audio_to_spectrogram(self, audio_path):
        """Convert audio file to log-mel spectrogram."""
        try:
            y, sr = librosa.load(audio_path, sr=config.SPECTROGRAM_SAMPLE_RATE)
            mel_spec = librosa.feature.melspectrogram(
                y=y, sr=sr, 
                n_mels=config.SPECTROGRAM_N_MELS, 
                hop_length=config.SPECTROGRAM_HOP_LENGTH
            )
            log_mel = librosa.power_to_db(mel_spec, ref=np.max)
            
            # Resize to model input shape
            log_mel_resized = tf.image.resize(
                log_mel[..., np.newaxis], 
                config.ACOUSTIC_MODEL_INPUT_SHAPE[:2]
            )
            return log_mel_resized.numpy()
        except Exception as e:
            if config.DEBUG_MODE:
                print(f"Error processing {audio_path}: {e}")
            return None


class ESC50DatasetLoader:
    """
    Loads ESC-50 dataset (environmental sounds - 50 classes).
    Used for pre-training acoustic model on diverse sounds.
    
    Dataset structure:
    - datasets/datasets audio/ESC-50-master/ESC-50-master/
        - audio/*.wav (2,000 files)
        - meta/esc50.csv (labels)
    """
    
    def __init__(self, base_path='d:/PREMONITOR/datasets/datasets audio/ESC-50-master/ESC-50-master'):
        self.base_path = base_path
        self.audio_dir = os.path.join(base_path, 'audio')
        self.meta_file = os.path.join(base_path, 'meta', 'esc50.csv')
        
    def load_environmental_sounds(self, fire_classes_only=False):
        """
        Load ESC-50 environmental sounds.
        
        Args:
            fire_classes_only: If True, only load fire/alarm/siren sounds (relevant to lab safety)
        
        Returns:
            spectrograms: np.array of shape (N, H, W, 1)
            labels: np.array of class IDs (0-49)
        """
        print("=" * 60)
        print("LOADING ESC-50 DATASET (Environmental Sounds)")
        print("=" * 60)
        
        # Read metadata
        df = pd.read_csv(self.meta_file)
        
        # Filter for safety-relevant classes if requested
        if fire_classes_only:
            safety_classes = ['fire_crackling', 'fireworks', 'siren', 'church_bells']
            df = df[df['category'].isin(safety_classes)]
            print(f"Filtering for safety-relevant classes: {safety_classes}")
        
        spectrograms = []
        labels = []
        
        print(f"Loading {len(df)} audio files...")
        for _, row in tqdm(df.iterrows(), total=len(df)):
            audio_path = os.path.join(self.audio_dir, row['filename'])
            if os.path.exists(audio_path):
                spec = self._audio_to_spectrogram(audio_path)
                if spec is not None:
                    spectrograms.append(spec)
                    labels.append(row['target'])
        
        print(f"Loaded {len(spectrograms)} samples")
        return np.array(spectrograms), np.array(labels)
    
    def _audio_to_spectrogram(self, audio_path):
        """Convert audio file to log-mel spectrogram."""
        try:
            y, sr = librosa.load(audio_path, sr=config.SPECTROGRAM_SAMPLE_RATE)
            mel_spec = librosa.feature.melspectrogram(
                y=y, sr=sr, 
                n_mels=config.SPECTROGRAM_N_MELS, 
                hop_length=config.SPECTROGRAM_HOP_LENGTH
            )
            log_mel = librosa.power_to_db(mel_spec, ref=np.max)
            log_mel_resized = tf.image.resize(
                log_mel[..., np.newaxis], 
                config.ACOUSTIC_MODEL_INPUT_SHAPE[:2]
            )
            return log_mel_resized.numpy()
        except Exception as e:
            if config.DEBUG_MODE:
                print(f"Error processing {audio_path}: {e}")
            return None


class UrbanSound8KDatasetLoader:
    """
    Loads UrbanSound8K dataset (8,732 urban sounds in 10 classes).
    Used for negative examples (non-anomaly environmental sounds).
    
    Dataset structure:
    - datasets/datasets audio/urbansound8kdataset/
        - fold1/*.wav, fold2/*.wav, ..., fold10/*.wav
        - UrbanSound8K.csv (metadata)
    """
    
    def __init__(self, base_path='d:/PREMONITOR/datasets/datasets audio/urbansound8kdataset'):
        self.base_path = base_path
        self.meta_file = os.path.join(base_path, 'UrbanSound8K.csv')
        
    def load_urban_sounds(self, folds=None):
        """
        Load UrbanSound8K audio files.
        
        Args:
            folds: List of fold numbers to load (1-10). If None, load all.
        
        Returns:
            spectrograms: np.array of shape (N, H, W, 1)
            labels: np.array of class IDs
        """
        print("=" * 60)
        print("LOADING URBANSOUND8K DATASET")
        print("=" * 60)
        
        df = pd.read_csv(self.meta_file)
        
        if folds is not None:
            df = df[df['fold'].isin(folds)]
            print(f"Loading folds: {folds}")
        
        spectrograms = []
        labels = []
        
        print(f"Loading {len(df)} audio files...")
        for _, row in tqdm(df.iterrows(), total=len(df)):
            audio_path = os.path.join(self.base_path, f"fold{row['fold']}", row['slice_file_name'])
            if os.path.exists(audio_path):
                spec = self._audio_to_spectrogram(audio_path)
                if spec is not None:
                    spectrograms.append(spec)
                    labels.append(row['classID'])
        
        print(f"Loaded {len(spectrograms)} samples")
        return np.array(spectrograms), np.array(labels)
    
    def _audio_to_spectrogram(self, audio_path):
        """Convert audio file to log-mel spectrogram."""
        try:
            y, sr = librosa.load(audio_path, sr=config.SPECTROGRAM_SAMPLE_RATE)
            mel_spec = librosa.feature.melspectrogram(
                y=y, sr=sr, 
                n_mels=config.SPECTROGRAM_N_MELS, 
                hop_length=config.SPECTROGRAM_HOP_LENGTH
            )
            log_mel = librosa.power_to_db(mel_spec, ref=np.max)
            log_mel_resized = tf.image.resize(
                log_mel[..., np.newaxis], 
                config.ACOUSTIC_MODEL_INPUT_SHAPE[:2]
            )
            return log_mel_resized.numpy()
        except Exception as e:
            if config.DEBUG_MODE:
                print(f"Error processing {audio_path}: {e}")
            return None


# ============================================================================
# THERMAL DATASET LOADERS
# ============================================================================

class FLIRDatasetLoader:
    """
    Loads FLIR ADAS v2 dataset (21,488 thermal images with COCO annotations).
    Perfect for pre-training thermal model on large-scale data.
    
    Dataset structure:
    - datasets/thermal camera dataset/FLIR_ADAS_v2/
        - images_thermal_train/data/*.jpeg
        - images_thermal_val/data/*.jpeg
        - video_thermal_train/coco.json
        - video_thermal_val/coco.json
    """
    
    def __init__(self, base_path='d:/PREMONITOR/datasets/thermal camera dataset/FLIR_ADAS_v2'):
        self.base_path = base_path
        self.train_dir = os.path.join(base_path, 'images_thermal_train', 'data')
        self.val_dir = os.path.join(base_path, 'images_thermal_val', 'data')
        self.train_anno = os.path.join(base_path, 'video_thermal_train', 'coco.json')
        self.val_anno = os.path.join(base_path, 'video_thermal_val', 'coco.json')
        
    def load_thermal_images_for_pretraining(self, include_val=True):
        """
        Load all FLIR thermal images for self-supervised pre-training.
        No labels needed - used for SimSiam contrastive learning.
        
        Returns:
            image_paths: List of paths to thermal images
        """
        print("=" * 60)
        print("LOADING FLIR ADAS V2 DATASET (Thermal Pre-training)")
        print("=" * 60)
        
        image_paths = []
        
        # Load training images
        if os.path.exists(self.train_dir):
            train_images = glob.glob(os.path.join(self.train_dir, '*.jpeg'))
            image_paths.extend(train_images)
            print(f"Found {len(train_images)} training images")
        
        # Load validation images
        if include_val and os.path.exists(self.val_dir):
            val_images = glob.glob(os.path.join(self.val_dir, '*.jpeg'))
            image_paths.extend(val_images)
            print(f"Found {len(val_images)} validation images")
        
        print(f"Total thermal images for pre-training: {len(image_paths)}")
        return image_paths
    
    def create_tf_dataset(self, image_paths, batch_size=32):
        """Create TensorFlow dataset for efficient loading."""
        path_ds = tf.data.Dataset.from_tensor_slices(image_paths)
        
        def load_image(path):
            img = tf.io.read_file(path)
            img = tf.image.decode_jpeg(img, channels=3)
            img = tf.image.resize(img, config.THERMAL_MODEL_INPUT_SHAPE[:2])
            img = tf.cast(img, tf.float32) / 255.0
            return img
        
        dataset = path_ds.map(load_image, num_parallel_calls=tf.data.AUTOTUNE)
        dataset = dataset.shuffle(1024).batch(batch_size).prefetch(tf.data.AUTOTUNE)
        return dataset


class AAUVAPTrimodalDatasetLoader:
    """
    Loads AAU VAP Trimodal dataset (RGB + Thermal + Depth with annotations).
    Used for fine-tuning thermal model with labeled person/anomaly data.
    
    Dataset structure:
    - datasets/thermal camera dataset/trimodaldataset/TrimodalDataset/
        - Scene 1/SyncT/*.png (4,694 thermal images)
        - Scene 1/SyncRGB/*.png
        - Scene 1/annotations.csv
        - Scene 2/, Scene 3/ (similar structure)
    """
    
    def __init__(self, base_path='d:/PREMONITOR/datasets/thermal camera dataset/trimodaldataset/TrimodalDataset'):
        self.base_path = base_path
        self.scenes = ['Scene 1', 'Scene 2', 'Scene 3']
        
    def load_thermal_images_with_labels(self, scenes_to_use=None):
        """
        Load thermal images with person annotations for fine-tuning.
        
        Args:
            scenes_to_use: List of scene names. If None, use all scenes.
        
        Returns:
            images: np.array of thermal images
            labels: np.array of binary labels (0=no person, 1=person detected)
        """
        print("=" * 60)
        print("LOADING AAU VAP TRIMODAL DATASET (Labeled Thermal)")
        print("=" * 60)
        
        if scenes_to_use is None:
            scenes_to_use = self.scenes
        
        all_image_paths = []
        all_labels = []
        
        for scene in scenes_to_use:
            scene_path = os.path.join(self.base_path, scene)
            thermal_dir = os.path.join(scene_path, 'SyncT')
            anno_file = os.path.join(scene_path, 'annotations.csv')
            
            if not os.path.exists(thermal_dir):
                print(f"Warning: {thermal_dir} not found, skipping...")
                continue
            
            # Load annotations if available
            has_labels = os.path.exists(anno_file)
            if has_labels:
                df = pd.read_csv(anno_file)
                print(f"Loaded {len(df)} annotations from {scene}")
            
            # Get all thermal images
            thermal_images = sorted(glob.glob(os.path.join(thermal_dir, '*.png')))
            print(f"Found {len(thermal_images)} thermal images in {scene}")
            
            # For now, assume all images with annotations have people (label=1)
            # Images without annotations are normal (label=0)
            # You can refine this based on actual annotation content
            for img_path in thermal_images:
                all_image_paths.append(img_path)
                # Simple heuristic: if annotations exist, assume supervised data
                all_labels.append(1 if has_labels else 0)
        
        print(f"\nTotal images: {len(all_image_paths)}")
        print(f"  - With annotations: {np.sum(np.array(all_labels) == 1)}")
        print(f"  - Without annotations: {np.sum(np.array(all_labels) == 0)}")
        
        return all_image_paths, np.array(all_labels)


# ============================================================================
# TIME-SERIES DATASET LOADERS
# ============================================================================

class TurbofanDatasetLoader:
    """
    Loads NASA Turbofan Engine Degradation dataset.
    Perfect for LSTM Autoencoder training (predictive maintenance).
    
    Dataset structure:
    - datasets/time-series anomaly detection datasets/
        17.+Turbofan+Engine+Degradation+Simulation+Data+Set+2/
          17. Turbofan Engine Degradation Simulation Data Set 2/
            - train_FD001.txt, test_FD001.txt, RUL_FD001.txt
            - train_FD002.txt, test_FD002.txt, RUL_FD002.txt
            ... (4 datasets total)
    """
    
    def __init__(self, base_path='d:/PREMONITOR/datasets/time-series anomaly detection datasets/17.+Turbofan+Engine+Degradation+Simulation+Data+Set+2/17. Turbofan Engine Degradation Simulation Data Set 2'):
        self.base_path = base_path
        
    def load_turbofan_data(self, dataset_id='FD001'):
        """
        Load Turbofan engine sensor data.
        
        Args:
            dataset_id: 'FD001', 'FD002', 'FD003', or 'FD004'
        
        Returns:
            X_train: Training sequences (normal operation)
            X_test: Test sequences (degradation)
            y_rul: Remaining Useful Life labels for test data
        """
        print("=" * 60)
        print(f"LOADING TURBOFAN DATASET ({dataset_id})")
        print("=" * 60)
        
        train_file = os.path.join(self.base_path, f'train_{dataset_id}.txt')
        test_file = os.path.join(self.base_path, f'test_{dataset_id}.txt')
        rul_file = os.path.join(self.base_path, f'RUL_{dataset_id}.txt')
        
        # Check if extraction is needed
        if not os.path.exists(train_file):
            print(f"ERROR: Dataset files not found!")
            print(f"Expected: {train_file}")
            print("Please extract the dataset first using the extraction script.")
            return None, None, None
        
        # Load training data
        train_df = pd.read_csv(train_file, sep=' ', header=None)
        train_df.dropna(axis=1, inplace=True)  # Remove NaN columns
        
        # Load test data
        test_df = pd.read_csv(test_file, sep=' ', header=None)
        test_df.dropna(axis=1, inplace=True)
        
        # Load RUL labels
        rul_df = pd.read_csv(rul_file, header=None)
        
        print(f"Training samples: {len(train_df)}")
        print(f"Test samples: {len(test_df)}")
        print(f"RUL labels: {len(rul_df)}")
        
        # Columns: [unit_id, time_cycles, op_setting1, op_setting2, op_setting3, sensor1, ..., sensor21]
        sensor_cols = list(range(5, 26))  # 21 sensor readings
        
        X_train = train_df[sensor_cols].values
        X_test = test_df[sensor_cols].values
        y_rul = rul_df.values.flatten()
        
        return X_train, X_test, y_rul


class SECOMDatasetLoader:
    """
    Loads SECOM dataset (semiconductor manufacturing data).
    Used for anomaly detection in time-series sensor data.
    
    Dataset structure:
    - datasets/time-series anomaly detection datasets/secom/
        - secom.data (sensor readings)
        - secom_labels.data (pass/fail labels)
    """
    
    def __init__(self, base_path='d:/PREMONITOR/datasets/time-series anomaly detection datasets/secom'):
        self.base_path = base_path
        self.data_file = os.path.join(base_path, 'secom.data')
        self.labels_file = os.path.join(base_path, 'secom_labels.data')
        
    def load_secom_data(self):
        """
        Load SECOM semiconductor manufacturing data.
        
        Returns:
            X: Sensor readings (590 features)
            y: Binary labels (0=pass, 1=fail)
        """
        print("=" * 60)
        print("LOADING SECOM DATASET")
        print("=" * 60)
        
        if not os.path.exists(self.data_file):
            print(f"ERROR: Dataset not found at {self.data_file}")
            print("Please extract the dataset first.")
            return None, None
        
        # Load data (space-separated, NaN represented as empty)
        X = pd.read_csv(self.data_file, sep=' ', header=None).values
        
        # Load labels
        y = pd.read_csv(self.labels_file, sep=' ', header=None).values[:, 0]
        
        print(f"Samples: {X.shape[0]}")
        print(f"Features: {X.shape[1]}")
        print(f"Anomalies: {np.sum(y == 1)} ({100*np.mean(y):.2f}%)")
        
        return X, y


# ============================================================================
# UNIFIED DATA LOADER
# ============================================================================

def load_all_datasets_for_training():
    """
    Master function to load all datasets for comprehensive training.
    This is the main entry point for your training pipeline.
    
    Returns:
        Dictionary containing all loaded datasets ready for training.
    """
    print("\n" + "=" * 80)
    print(" " * 20 + "PREMONITOR COMPREHENSIVE DATASET LOADER")
    print("=" * 80)
    
    datasets = {}
    
    # Audio datasets
    print("\n### LOADING AUDIO DATASETS ###\n")
    
    try:
        mimii_loader = MIMIIDatasetLoader()
        X_mimii, y_mimii = mimii_loader.load_all_machine_sounds(use_all_ids=True)
        datasets['mimii'] = {'X': X_mimii, 'y': y_mimii}
    except Exception as e:
        print(f"MIMII loading failed: {e}")
    
    try:
        esc50_loader = ESC50DatasetLoader()
        X_esc50, y_esc50 = esc50_loader.load_environmental_sounds(fire_classes_only=False)
        datasets['esc50'] = {'X': X_esc50, 'y': y_esc50}
    except Exception as e:
        print(f"ESC-50 loading failed: {e}")
    
    try:
        urban_loader = UrbanSound8KDatasetLoader()
        X_urban, y_urban = urban_loader.load_urban_sounds(folds=[1, 2, 3])  # Load first 3 folds
        datasets['urbansound8k'] = {'X': X_urban, 'y': y_urban}
    except Exception as e:
        print(f"UrbanSound8K loading failed: {e}")
    
    # Thermal datasets
    print("\n### LOADING THERMAL DATASETS ###\n")
    
    try:
        flir_loader = FLIRDatasetLoader()
        flir_paths = flir_loader.load_thermal_images_for_pretraining(include_val=True)
        datasets['flir'] = {'paths': flir_paths}
    except Exception as e:
        print(f"FLIR loading failed: {e}")
    
    try:
        aau_loader = AAUVAPTrimodalDatasetLoader()
        aau_paths, aau_labels = aau_loader.load_thermal_images_with_labels()
        datasets['aau_vap'] = {'paths': aau_paths, 'labels': aau_labels}
    except Exception as e:
        print(f"AAU VAP loading failed: {e}")
    
    # Time-series datasets
    print("\n### LOADING TIME-SERIES DATASETS ###\n")
    
    try:
        turbofan_loader = TurbofanDatasetLoader()
        X_train, X_test, y_rul = turbofan_loader.load_turbofan_data(dataset_id='FD001')
        if X_train is not None:
            datasets['turbofan'] = {'X_train': X_train, 'X_test': X_test, 'y_rul': y_rul}
    except Exception as e:
        print(f"Turbofan loading failed: {e}")
    
    try:
        secom_loader = SECOMDatasetLoader()
        X_secom, y_secom = secom_loader.load_secom_data()
        if X_secom is not None:
            datasets['secom'] = {'X': X_secom, 'y': y_secom}
    except Exception as e:
        print(f"SECOM loading failed: {e}")
    
    print("\n" + "=" * 80)
    print(" " * 20 + "DATASET LOADING COMPLETE!")
    print("=" * 80)
    print(f"\nSuccessfully loaded {len(datasets)} datasets:")
    for name in datasets.keys():
        print(f"  ✓ {name}")
    print("\n")
    
    return datasets


if __name__ == "__main__":
    # Test loading all datasets
    datasets = load_all_datasets_for_training()
    
    print("\n### DATASET SUMMARY ###")
    for name, data in datasets.items():
        print(f"\n{name.upper()}:")
        for key, value in data.items():
            if isinstance(value, np.ndarray):
                print(f"  {key}: shape {value.shape}, dtype {value.dtype}")
            elif isinstance(value, list):
                print(f"  {key}: {len(value)} items")
