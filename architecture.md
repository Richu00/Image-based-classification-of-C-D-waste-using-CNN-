# Model Architecture

## Overview

This project uses **Transfer Learning** with **MobileNetV2** pre-trained on ImageNet.

```
Input Image (any size)
        ↓
  Resize to 224×224
        ↓
  Normalise (ImageNet mean/std)
        ↓
┌─────────────────────────────┐
│   MobileNetV2 Backbone      │  ← FROZEN (weights don't change)
│   (18 convolutional layers) │    Except last 3 layers which fine-tune
│   Detects edges, textures,  │
│   shapes, material surfaces │
└─────────────────────────────┘
        ↓  1,280 features
┌─────────────────────────────┐
│   New Linear Layer          │  ← TRAINED FROM SCRATCH
│   nn.Linear(1280 → 5)       │    Only this layer + last 3 backbone layers
└─────────────────────────────┘
        ↓
  5 confidence scores
  [concrete, glass, metal, plastic, wood]
        ↓
  Softmax → probabilities (sum to 100%)
        ↓
  Highest = predicted class
```

## Why MobileNetV2?

- Only **3.4 million parameters** (vs VGG-16's 138 million)
- Pre-trained on **1.2 million ImageNet images**
- Trains in **5–10 minutes** on a standard GPU
- Competitive accuracy (~72% top-1 on ImageNet)

## Transfer Learning Strategy

**Feature Extraction + Partial Fine-Tuning:**

1. All backbone layers frozen first
2. Last 3 layers (`model.features[-3:]`) unfrozen
3. New 5-output classification head added
4. Only unfrozen layers + new head are updated during training

This approach is used because:
- The early layers already know how to detect edges, textures, shapes
- The last layers learn material-specific features (concrete texture vs rock)
- Training only a few layers is fast and prevents overfitting on small datasets

## Training Configuration

| Parameter | Value | Reason |
|-----------|-------|--------|
| Optimiser | Adam | Adaptive learning rate — stable convergence |
| Learning rate | 0.0001 | Small — protects pre-trained backbone weights |
| Batch size | 16 | Balances memory and gradient quality |
| Epochs | 15 | Fine-tuning needs more passes than pure feature extraction |
| Loss | Cross-Entropy | Standard for multi-class classification |

## Data Augmentation (Training Only)

Applied to training images only — validation images are never augmented:

- `RandomCrop(224)` from a 256×256 resize
- `RandomHorizontalFlip()` — 50% chance
- `RandomVerticalFlip(p=0.2)` — 20% chance
- `RandomRotation(20)` — up to ±20 degrees
- `ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2, hue=0.05)`

**Purpose:** Forces the model to learn material texture rather than memorising specific angles and lighting conditions. Critical for distinguishing concrete chunks from rock.
