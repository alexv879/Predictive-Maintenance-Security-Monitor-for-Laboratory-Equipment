# Pretrained Weights Status

**Date**: October 29, 2025  
**Status**: Partially Downloaded

---

## Downloaded Models

### ✅ Xception ImageNet (thermal_xception)
- **Size**: 79.8 MB
- **Location**: `models/pretrained/xception_imagenet_notop.h5`
- **MD5**: Verified
- **Use Case**: High-accuracy thermal feature extractor
- **Architecture**: Xception (no top layers) pretrained on ImageNet
- **License**: MIT

**Integration Status**: Ready to use in train.py

---

## Failed Downloads

### ⚠️ MobileNetV2 ImageNet (thermal_mobilenetv2)
- **Issue**: MD5 mismatch - Google may have updated the file
- **Expected MD5**: `5d48d72eca093e0a5f2be2872c3b7c4c`
- **Actual MD5**: `321911b381f6fd09b744356f6796ee18`
- **File Location**: `models/pretrained/mobilenetv2_imagenet.h5` (downloaded but not verified)
- **Workaround**: Use Keras API directly during training

```python
# Alternative approach in train.py
from tensorflow.keras.applications import MobileNetV2

# Load pretrained weights automatically from Keras
base_model = MobileNetV2(
    input_shape=(224, 224, 3),
    include_top=False,
    weights='imagenet'  # Downloads automatically if not cached
)
```

### ⚠️ YAMNet AudioSet (acoustic_yamnet)
- **Issue**: HTTP 403 Forbidden - TF Hub requires authentication or API key
- **URL**: `https://storage.googleapis.com/tfhub-modules/google/yamnet/1.tar.gz`
- **Workaround**: Use TensorFlow Hub API during training

```python
# Alternative approach in train.py
import tensorflow_hub as hub

# Load YAMNet directly from TF Hub (handles authentication)
yamnet_model = hub.load('https://tfhub.dev/google/yamnet/1')
```

---

## Usage in Training

### Using Xception (Downloaded)

```python
from tensorflow.keras.models import load_model

# Load pretrained Xception
xception_base = load_model('models/pretrained/xception_imagenet_notop.h5')

# Freeze backbone
xception_base.trainable = False

# Add custom head for thermal anomaly detection
model = keras.Sequential([
    xception_base,
    GlobalAveragePooling2D(),
    Dense(256, activation='relu'),
    Dropout(0.5),
    Dense(1, activation='sigmoid')  # Binary anomaly detection
])
```

### Using MobileNetV2 (Keras API)

```python
from tensorflow.keras.applications import MobileNetV2

# Load from Keras (auto-downloads to ~/.keras/models/)
mobilenet_base = MobileNetV2(
    input_shape=(224, 224, 3),
    include_top=False,
    weights='imagenet'
)

# Freeze and add custom head
mobilenet_base.trainable = False
model = keras.Sequential([
    mobilenet_base,
    GlobalAveragePooling2D(),
    Dense(128, activation='relu'),
    Dropout(0.3),
    Dense(1, activation='sigmoid')
])
```

### Using YAMNet (TF Hub)

```python
import tensorflow_hub as hub
import tensorflow as tf

# Load YAMNet from TF Hub
yamnet_model = hub.load('https://tfhub.dev/google/yamnet/1')

# Extract embedding layer
yamnet_embedding_layer = hub.KerasLayer(
    'https://tfhub.dev/google/yamnet/1',
    trainable=False,
    arguments=dict(output_key='embedding')
)

# Build acoustic anomaly model
model = keras.Sequential([
    Input(shape=(None,)),  # Variable-length audio
    yamnet_embedding_layer,
    Dense(512, activation='relu'),
    Dropout(0.5),
    Dense(256, activation='relu'),
    Dense(1, activation='sigmoid')
])
```

---

## Next Steps

### Option 1: Use Keras/TF Hub APIs (Recommended)
- ✅ No manual downloads needed
- ✅ Automatic caching in `~/.keras/models/` or `~/.tfhub_modules/`
- ✅ Always get latest weights
- ✅ Simpler integration

**Update train.py** to use Keras APIs instead of manual file loading.

### Option 2: Alternative Download Sources
- Update `fetch_pretrained_weights.py` with alternative URLs
- Check Keras Applications source code for current URLs
- Use PyTorch Hub and convert to TensorFlow (more complex)

### Option 3: Fine-tune Existing Models
- Start with Xception (already downloaded)
- Train thermal models with Xception backbone
- For acoustic, use TF Hub directly (no download needed)

---

## Verification Commands

```powershell
# List downloaded weights
ls models\pretrained\

# Check registry
cat models\pretrained\registry.json

# Verify file integrity
python scripts\fetch_pretrained_weights.py --model list
```

---

## Training Integration

### Modified train.py Example

```python
def build_thermal_model_with_pretrained(use_xception=True):
    """Build thermal model with pretrained backbone"""
    
    if use_xception:
        # Use downloaded Xception
        if os.path.exists('models/pretrained/xception_imagenet_notop.h5'):
            logger.info("Loading pretrained Xception from local file")
            base_model = load_model('models/pretrained/xception_imagenet_notop.h5')
        else:
            logger.info("Downloading Xception from Keras")
            from tensorflow.keras.applications import Xception
            base_model = Xception(
                input_shape=(224, 224, 3),
                include_top=False,
                weights='imagenet'
            )
    else:
        # Fallback to MobileNetV2 via Keras API
        logger.info("Loading MobileNetV2 from Keras")
        from tensorflow.keras.applications import MobileNetV2
        base_model = MobileNetV2(
            input_shape=(224, 224, 3),
            include_top=False,
            weights='imagenet'
        )
    
    # Freeze backbone
    base_model.trainable = False
    
    # Add anomaly detection head
    model = keras.Sequential([
        base_model,
        GlobalAveragePooling2D(),
        Dense(256, activation='relu'),
        Dropout(0.5),
        Dense(1, activation='sigmoid')
    ])
    
    return model


def build_acoustic_model_with_yamnet():
    """Build acoustic model with YAMNet embeddings"""
    import tensorflow_hub as hub
    
    # Load YAMNet embedding layer from TF Hub
    yamnet_layer = hub.KerasLayer(
        'https://tfhub.dev/google/yamnet/1',
        trainable=False,
        arguments=dict(output_key='embedding')
    )
    
    model = keras.Sequential([
        Input(shape=(None,)),
        yamnet_layer,
        Dense(512, activation='relu'),
        Dropout(0.5),
        Dense(256, activation='relu'),
        Dense(1, activation='sigmoid')
    ])
    
    return model
```

---

## Recommendations

**For Thermal Models**:
1. ✅ Use Xception (downloaded) for highest accuracy
2. Use MobileNetV2 via Keras API for speed/efficiency trade-off
3. Consider EfficientNetV2 via Keras for best balance

**For Acoustic Models**:
1. Use YAMNet via TF Hub (handles download automatically)
2. Consider PANNs (Pretrained Audio Neural Networks) as alternative
3. Fallback: Train custom CNN on spectrograms from scratch

**Training Strategy**:
1. Start with frozen pretrained backbone
2. Train only custom head layers (fast, prevents overfitting)
3. After convergence, unfreeze top layers of backbone
4. Fine-tune with very low learning rate (1e-5 to 1e-6)

---

**Status Updated**: October 29, 2025
