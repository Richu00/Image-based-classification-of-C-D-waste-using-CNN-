# 🏗️ C&D Waste Material Classifier

> Image-based classification of Construction & Demolition waste using **MobileNetV2 Transfer Learning** — achieves **90.2% validation accuracy** on 5 material classes.

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.10-red?logo=pytorch)](https://pytorch.org)
[![Accuracy](https://img.shields.io/badge/Val%20Accuracy-90.2%25-green)]()
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## What This Does

This project trains a CNN that automatically identifies **5 types of C&D waste materials** from photographs:

| Class | Description |
|-------|-------------|
| `concrete` | Broken slabs, rubble chunks, aggregate fragments |
| `glass` | Broken panels, bottles, glazing fragments |
| `metal` | Rebar, pipes, sheets, wire |
| `plastic` | Pipes, fittings, packaging fragments |
| `wood` | Planks, plywood, formwork offcuts |

**Key facts:**
- Trained on **5,418 images** (4,057 train / 1,361 val)
- Peak validation accuracy: **90.2%** at Epoch 4
- Runs on **CPU or GPU** — auto-detected
- Built with **Transfer Learning** — only the final layer is trained from scratch
- Includes a **correction system** — fix wrong predictions without retraining

---

## Project Structure

```
cdw-classifier/
│
├── train_model.py        # Train the model on your dataset
├── test_model.py         # Classify images + correction system
│
├── dataset/              # YOUR IMAGES GO HERE (not included in repo)
│   ├── train/
│   │   ├── concrete/
│   │   ├── glass/
│   │   ├── metal/
│   │   ├── plastic/
│   │   └── wood/
│   └── val/
│       ├── concrete/
│       ├── glass/
│       ├── metal/
│       ├── plastic/
│       └── wood/
│
├── corrections.json      # Auto-created when you correct predictions
├── waste_classifier.pth  # Auto-created after training
│
├── docs/
│   └── architecture.md   # How the model works (technical details)
│
├── samples/
│   └── README.md         # Where to put test images
│
├── requirements.txt      # Python dependencies
├── .gitignore            # Keeps large files out of Git
└── README.md             # This file
```

---

## Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/cdw-classifier.git
cd cdw-classifier
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Add your dataset
Put images in the `dataset/` folder following the structure above.
See [Dataset Sources](#dataset-sources) below for where to get images.

### 4. Train
```bash
python train_model.py
```
Training takes ~40 min/epoch on CPU, ~5 min/epoch on GPU.
The best model is saved automatically as `waste_classifier.pth`.

### 5. Classify an image
```bash
python test_model.py path/to/image.jpg
```

---

## Training Results

| Epoch | Training Loss | Val Accuracy |
|-------|--------------|--------------|
| 1/5   | 0.534        | 88.5%        |
| 2/5   | 0.318        | 88.5%        |
| 3/5   | 0.289        | 89.4%        |
| **4/5** | **0.286**  | **90.2% ★**  |
| 5/5   | 0.268        | 89.6%        |

---

## Correction System

If the model classifies an image incorrectly, you can correct it without retraining:

```bash
# Classify an image — it will ask if the result is correct
python test_model.py rock.jpeg

# View all saved corrections
python test_model.py --corrections

# Remove a correction
python test_model.py --remove rock.jpeg
```

Corrections are saved to `corrections.json` and remembered permanently.

---

## Dataset Sources

| Class | Recommended Source |
|-------|--------------------|
| Concrete + Wood | [CODD Dataset — Mendeley Data](https://data.mendeley.com/datasets/wds85kt64j/3) |
| Glass + Metal | [TrashNet — GitHub](https://github.com/garythung/trashnet) |
| Plastic | [Kaggle Garbage Classification](https://www.kaggle.com/datasets/sumn2u/garbage-classification-v2) |

---

## Comparison with Recent Literature (2021–2026)

| Study | Architecture | Accuracy | Limitation |
|-------|-------------|----------|------------|
| Davis et al. (2021) | Custom CNN | 94.0% | No transfer learning |
| Lin et al. (2023) | ResNet-152 | 93.8% | 1,186s training time |
| Demetriou et al. (2023) | YOLOv8 | mAP 85% | Detection only |
| Mishra et al. (2024) | DenseNet+SVM | 96.2% | High complexity |
| HR-ViT (2025) | ResNet50+ViT | 98.27% | Needs massive GPU |
| **This project** | **MobileNetV2** | **90.2%** | **Beginner-accessible** |

---

## Requirements

- Python 3.8+
- PyTorch 2.0+
- torchvision 0.15+
- Pillow 9.0+

See `requirements.txt` for exact versions.

---

## License

MIT License — free to use, modify, and distribute.
See [LICENSE](LICENSE) for details.

---

## Citation

If you use this project in research, please cite:

```
C&D Waste Material Classifier using MobileNetV2 Transfer Learning (2025)
GitHub: https://github.com/YOUR_USERNAME/cdw-classifier
```
