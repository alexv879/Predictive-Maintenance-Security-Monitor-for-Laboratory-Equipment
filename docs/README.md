# PREMONITOR - AI-Powered Anomaly Detection System

An intelligent monitoring system using thermal imaging, acoustic analysis, and sensor fusion to detect anomalies in real-time on Raspberry Pi hardware.

## Project Overview

Premonitor combines multiple AI models (CNN-based thermal analysis, acoustic spectrogram classification, and LSTM autoencoders) to provide robust anomaly detection with multi-modal sensor fusion. The system is designed to run on resource-constrained hardware (Raspberry Pi) using TensorFlow Lite for efficient inference.

## Quick Start (Windows PowerShell)

### 1. Prerequisites

- Python 3.8 or higher (tested with Python 3.13.5)
- Windows 10/11 with PowerShell
- ~10GB disk space for datasets
- (Optional) GPU for model training

### 2. Environment Setup

```powershell
# Clone or navigate to the project directory
cd D:\PREMONITOR

# Create a virtual environment (recommended)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 3. Verify Installation

```powershell
# Run dataset validation
python .\scripts\check_datasets.py --verbose

# Run smoke tests
python .\tests\test_datasets.py
```

## Project Structure

```
D:\PREMONITOR\
├── pythonsoftware/           # Core Python modules
│   ├── premonitor_main_py.py           # Main entry point
│   ├── premonitor_config_py.py         # Configuration settings
│   ├── premonitor_utils_py.py          # Data processing utilities
│   ├── premonitor_alert_manager_py.py  # Alert/notification system
│   ├── premonitor_mock_hardware_py.py  # Hardware simulation for testing
│   ├── premonitor_model_blueprints_py.py # AI model architectures
│   └── premonitor_train_models_py.py   # Model training scripts
│
├── notebooks/                # Jupyter notebooks for interactive development
│   ├── Premonitor_main_py.ipynb
│   ├── Premonitor_config_py.ipynb
│   └── ... (additional notebooks)
│
├── datasets/                 # Dataset storage
│   ├── datasets audio/
│   │   ├── ESC-50-master/           # ESC-50 environmental sounds (2000 samples)
│   │   └── urbansound8kdataset/     # UrbanSound8K (8732 samples)
│   ├── thermal camera dataset/
│   │   └── trimodaldataset/         # Trimodal RGB-D-Thermal dataset
│   └── time-series anomaly detection datasets/
│
├── scripts/                  # Utility scripts
│   └── check_datasets.py     # Dataset validation tool
│
├── tests/                    # Test suite
│   ├── test_datasets.py      # Dataset validation tests
│   ├── test_imports.py       # Module import tests
│   └── run_all_tests.py      # Master test runner
│
├── models/                   # Trained AI models (.tflite files)
├── logs/                     # Application logs
├── config/                   # Device-specific configurations
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Datasets

### Audio Datasets

1. **ESC-50** - Environmental Sound Classification
   - Location: `datasets/datasets audio/ESC-50-master/ESC-50-master/`
   - Files: 2000 audio samples (.wav), 50 sound categories
   - Metadata: `meta/esc50.csv`
   - Status: ✓ Present and validated

2. **UrbanSound8K** - Urban sound classification
   - Location: `datasets/datasets audio/urbansound8kdataset/`
   - Files: 8732 audio samples across 10 urban sound classes
   - Metadata: `UrbanSound8K.csv`
   - Status: ✓ Present and validated

### Thermal/Visual Datasets

1. **Trimodal Dataset** - RGB-Depth-Thermal synchronized frames
   - Location: `datasets/thermal camera dataset/trimodaldataset/`
   - Scenes: 3 annotated scenes
   - Metadata: `trimodal-thermal.json`, `trimodal-rgb.json`, `trimodal-depth.json`
   - Images: 11,537 depth images (thermal/RGB in metadata)
   - Status: ✓ Present and validated

### Dataset Validation

Run the automated dataset checker:

```powershell
python .\scripts\check_datasets.py --verbose
```

This will report:
- Dataset presence and integrity
- File counts per dataset
- Missing or incomplete datasets
- CSV/JSON metadata validation

## Running the Application

### For Development/Testing (Mock Hardware)

The main application uses mock hardware by default for testing:

```powershell
cd pythonsoftware
python premonitor_main_py.py
```

**Note**: This requires trained AI models in the `models/` directory. See "Training Models" below.

### Training AI Models

Before running the main application, you need to train the AI models:

```powershell
cd pythonsoftware
python premonitor_train_models_py.py
```

This will:
1. Load datasets from the `datasets/` directory
2. Train thermal anomaly detection model (SimSiam + Xception)
3. Train acoustic anomaly detection model (CNN on spectrograms)
4. Export quantized TensorFlow Lite models to `models/` directory

**Requirements for training**:
- All dependencies installed (`pip install -r requirements.txt`)
- Datasets present and validated
- Recommended: GPU with CUDA support for faster training

### Configuration

Edit `pythonsoftware/premonitor_config_py.py` for:
- Model paths
- Sensor thresholds
- Alert configuration
- Debug settings

For production deployment, create a `device_config.json` file to override defaults per device.

### Email Alerts Setup

To enable email alerts, set environment variables:

```powershell
$env:EMAIL_SENDER_ADDRESS = "your_email@gmail.com"
$env:EMAIL_SENDER_PASSWORD = "your_app_password"
```

For Gmail, you need to create an [App Password](https://support.google.com/accounts/answer/185833).

## Testing

### Run All Tests

```powershell
python .\tests\run_all_tests.py
```

### Individual Test Suites

```powershell
# Dataset validation tests
python .\tests\test_datasets.py

# Module import tests (requires dependencies installed)
python .\tests\test_imports.py
```

### Quality Gates

- **Build**: All Python files must compile without syntax errors ✓
- **Datasets**: Required datasets present and validated ✓
- **Imports**: Core modules must import successfully (requires full dependencies)
- **Functionality**: Smoke tests for key functions (pending model training)

## Development Workflow

### Notebooks vs Python Files

The project includes both `.py` files and `.ipynb` notebooks:

- **Python files** (`pythonsoftware/*.py`): Production code for deployment on Raspberry Pi
- **Notebooks** (`notebooks/*.ipynb`): Interactive development, experimentation, visualization

For deployment, use the Python files. For development/training, you may prefer notebooks.

### Module Naming Convention

Python modules use the naming pattern `premonitor_<module>_py.py` to match the original notebook structure. When importing:

```python
# From within pythonsoftware directory or with proper PYTHONPATH:
import config              # imports premonitor_config_py.py
import utils               # imports premonitor_utils_py.py
import alert_manager       # imports premonitor_alert_manager_py.py
```

### Adding New Features

1. Create/modify module in `pythonsoftware/`
2. Update corresponding notebook if exists
3. Add tests to `tests/`
4. Update `requirements.txt` if new dependencies added
5. Run quality checks before committing

## Hardware Deployment (Future)

To deploy on actual Raspberry Pi hardware with real sensors:

1. Replace `import mock_hardware as hardware` with `import hardware_drivers as hardware` in `premonitor_main_py.py`
2. Implement `hardware_drivers.py` with actual sensor interfaces:
   - Thermal camera (e.g., FLIR Lepton via `pylepton`)
   - USB microphone (via `pyaudio`)
   - Gas sensors (via `RPi.GPIO` and ADC chips)
3. Install Raspberry Pi specific dependencies (currently commented in `requirements.txt`)
4. Copy trained `.tflite` models to Pi's `models/` directory
5. Set up systemd service for auto-start

## Troubleshooting

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'config'`

**Solution**: Ensure you're running from the `pythonsoftware/` directory or add it to PYTHONPATH:

```powershell
cd pythonsoftware
python premonitor_main_py.py
```

### Missing Dependencies

**Problem**: `No module named 'librosa'` or `No module named 'tensorflow'`

**Solution**: Install all required dependencies:

```powershell
python -m pip install -r requirements.txt
```

### Dataset Not Found

**Problem**: Application can't find datasets

**Solution**:
1. Run `python .\scripts\check_datasets.py --verbose` to identify missing datasets
2. Ensure datasets are in the correct directory structure
3. Check that ZIP files have been extracted if applicable

### Unicode Errors on Windows

**Problem**: `UnicodeEncodeError` when running tests

**Solution**: Tests have been updated to use ASCII characters. If you still see errors, set:

```powershell
$env:PYTHONIOENCODING = "utf-8"
```

## Known Issues

1. **Protobuf Version Warning**: TensorFlow may show protobuf compatibility warnings. These are non-critical and can be ignored for this project.
2. **NumPy Version**: SciPy requires NumPy < 2.3.0. Install compatible version: `pip install "numpy<2.0.0"`
3. **Thermal Images**: Trimodal dataset has depth images but thermal/RGB are referenced in JSON metadata only (not extracted from original dataset structure).

## Contributing

When contributing:

1. Run all tests before submitting: `python .\tests\run_all_tests.py`
2. Update documentation for any API changes
3. Follow PEP 8 style guidelines
4. Add tests for new functionality

## License

[Add license information]

## Acknowledgments

This project uses the following datasets:

- **ESC-50**: Piczak, K. J. (2015). ESC: Dataset for Environmental Sound Classification.
- **UrbanSound8K**: Salamon, J., Jacoby, C., & Bello, J. P. (2014). A Dataset and Taxonomy for Urban Sound Research.
- **Trimodal Dataset**: RGB-Depth-Thermal synchronized frames for person detection and tracking.

AI model architectures inspired by:
- Goyal & Rajapakse - SimSiam for anomaly detection
- Reis & Serôdio - LSTM Autoencoders for time-series
