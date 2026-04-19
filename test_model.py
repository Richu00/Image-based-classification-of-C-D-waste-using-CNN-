# ============================================================
#  C&D WASTE CLASSIFIER  –  TEST / PREDICT SCRIPT
#  WITH FEEDBACK & CORRECTION SYSTEM
#
#  NEW FEATURE: If the model gets an image wrong, you can
#  correct it on the spot. The correction is saved to a file
#  called  corrections.json  and remembered forever.
#
#  Next time you run the same image, it shows the correct
#  label instantly — no retraining needed.
#
#  HOW TO USE:
#  ─────────────────────────────────────────────────────────
#  Classify an image:
#    python test_model.py  C:\path\to\image.jpg
#
#  The model shows its prediction. If it's wrong, just type
#  the correct class when prompted. Done — it remembers.
#
#  View all saved corrections:
#    python test_model.py  --corrections
#
#  Remove a saved correction:
#    python test_model.py  --remove  C:\path\to\image.jpg
# ============================================================

import sys
import json
import os
import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image

# ── Configuration ─────────────────────────────────────────────
CLASS_NAMES = ["concrete", "glass", "metal", "plastic", "wood"]

# This file stores all your corrections automatically.
CORRECTIONS_FILE = "corrections.json"


# ════════════════════════════════════════════════════════════
#  CORRECTION SYSTEM
#  ─────────────────────────────────────────────────────────
#  All corrections are saved to corrections.json like this:
#
#  {
#    "C:\\CNN_Project\\rock.jpeg":   "concrete",
#    "C:\\CNN_Project\\bottle.jpg":  "plastic"
#  }
#
#  The image's full path is the key.
#  Next time you run the same image, the saved answer is
#  returned immediately — the model is not even called.
# ════════════════════════════════════════════════════════════

def load_corrections():
    """Read all saved corrections from corrections.json."""
    if os.path.exists(CORRECTIONS_FILE):
        with open(CORRECTIONS_FILE, "r") as f:
            return json.load(f)
    return {}   # No file yet → return empty dict

def save_correction(image_path, correct_class):
    """Add or update a correction and write it to disk."""
    corrections = load_corrections()
    abs_path    = os.path.abspath(image_path)   # Always use full path as key
    corrections[abs_path] = correct_class
    with open(CORRECTIONS_FILE, "w") as f:
        json.dump(corrections, f, indent=2)
    print(f"\n  [SAVED]  '{os.path.basename(image_path)}'  =  {correct_class.upper()}")
    print(f"           Remembered in {CORRECTIONS_FILE}\n")

def remove_correction(image_path):
    """Delete a previously saved correction."""
    corrections = load_corrections()
    abs_path    = os.path.abspath(image_path)
    if abs_path in corrections:
        old_label = corrections.pop(abs_path)
        with open(CORRECTIONS_FILE, "w") as f:
            json.dump(corrections, f, indent=2)
        print(f"\n  [REMOVED]  '{os.path.basename(image_path)}'  (was: {old_label})\n")
    else:
        print(f"\n  No correction found for: {os.path.basename(image_path)}\n")

def show_all_corrections():
    """Print every saved correction as a table."""
    corrections = load_corrections()
    if not corrections:
        print("\n  No corrections saved yet.")
        print(f"  Corrections will appear here after you correct a wrong prediction.\n")
        return
    print(f"\n  Saved corrections  ({len(corrections)} total)  →  {CORRECTIONS_FILE}")
    print("  " + "─" * 62)
    for path, label in corrections.items():
        filename = os.path.basename(path)
        print(f"  {filename:<45}  {label.upper()}")
    print("  " + "─" * 62 + "\n")


# ════════════════════════════════════════════════════════════
#  MODEL SETUP
# ════════════════════════════════════════════════════════════

model = models.mobilenet_v2(weights=None)

# Must match train_model.py exactly
for param in model.parameters():
    param.requires_grad = False

for param in model.features[-3:].parameters():   # last 3 layers unfrozen
    param.requires_grad = True

model.classifier[1] = nn.Linear(
    in_features  = model.classifier[1].in_features,
    out_features = len(CLASS_NAMES)
)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

if not os.path.exists("waste_classifier.pth"):
    print("\n  ERROR: waste_classifier.pth not found.")
    print("  Run  python train_model.py  first.\n")
    sys.exit(1)

model.load_state_dict(torch.load("waste_classifier.pth", map_location=device))
model = model.to(device)
model.eval()

# Image transform — no augmentation for inference
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std =[0.229, 0.224, 0.225])
])


# ════════════════════════════════════════════════════════════
#  CLASSIFY AN IMAGE
# ════════════════════════════════════════════════════════════

def classify_image(image_path):
    """
    Classify one image.
    Checks saved corrections first.
    If no correction exists, runs the model.
    Then asks the user if the result is correct.
    """

    abs_path    = os.path.abspath(image_path)
    filename    = os.path.basename(image_path)
    corrections = load_corrections()

    # ── Case 1: We already have a saved correction for this image ──
    if abs_path in corrections:
        saved = corrections[abs_path]
        print(f"\nImage: {filename}")
        print("─" * 42)
        print(f"  ⭐  CORRECTION ON FILE:  {saved.upper()}")
        print(f"      (You previously told the model this is {saved})")
        print("─" * 42)

        # Give the user a chance to update if it was wrong before
        reply = input("\n  Still correct? (y = yes / n = update / s = skip): ").strip().lower()
        if reply == "n":
            prompt_for_correction(image_path, saved)
        elif reply == "y":
            print(f"\n  Keeping: {saved.upper()}\n")
        # 's' or anything else = skip quietly
        return

    # ── Case 2: No saved correction — run the model ──────────────
    try:
        image = Image.open(image_path).convert("RGB")
    except FileNotFoundError:
        print(f"\n  ERROR: File not found → {image_path}\n")
        return

    # Prepare image and run model
    img_tensor = transform(image).unsqueeze(0).to(device)
    with torch.no_grad():
        output = model(img_tensor)

    probs      = torch.softmax(output, dim=1)[0] * 100
    best_idx   = probs.argmax().item()
    best_class = CLASS_NAMES[best_idx]
    best_score = probs[best_idx].item()

    # Print confidence bar chart
    print(f"\nImage: {filename}")
    print("─" * 42)
    for i, name in enumerate(CLASS_NAMES):
        pct    = probs[i].item()
        bar    = "█" * int(pct / 5)
        arrow  = " ←" if i == best_idx else ""
        print(f"  {name:<10}  {pct:5.1f}%  {bar}{arrow}")
    print("─" * 42)
    print(f"  → Predicted: {best_class.upper()}  ({best_score:.1f}% confident)\n")

    if best_score < 50:
        print("  ⚠  Low confidence — the model is unsure.\n")

    # Ask if the prediction is right
    prompt_for_correction(image_path, best_class)


def prompt_for_correction(image_path, current_label):
    """
    Ask the user if the label is correct.
    If not, let them choose the right class and save it.
    """
    reply = input(f"  Is '{current_label.upper()}' correct? (y / n / s=skip): ").strip().lower()

    if reply in ("y", "yes"):
        print(f"\n  ✔  Correct! No correction needed.\n")

    elif reply in ("n", "no"):
        print("\n  Choose the correct class:")
        for i, name in enumerate(CLASS_NAMES):
            print(f"    {i+1}. {name}")
        print()

        while True:
            choice = input("  Enter number (1–5) or class name: ").strip().lower()
            if choice.isdigit() and 1 <= int(choice) <= len(CLASS_NAMES):
                correct = CLASS_NAMES[int(choice) - 1]
                break
            elif choice in CLASS_NAMES:
                correct = choice
                break
            else:
                print(f"  Please enter 1–{len(CLASS_NAMES)} or: {', '.join(CLASS_NAMES)}")

        save_correction(image_path, correct)

    # 's' / 'skip' / anything else — do nothing
    else:
        print()


# ════════════════════════════════════════════════════════════
#  ENTRY POINT
# ════════════════════════════════════════════════════════════

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  python test_model.py  <image>           Classify an image")
        print("  python test_model.py  --corrections     Show all saved corrections")
        print("  python test_model.py  --remove <image>  Remove a correction")
        print(f"\nValid classes: {', '.join(CLASS_NAMES)}\n")

    elif sys.argv[1] == "--corrections":
        show_all_corrections()

    elif sys.argv[1] == "--remove":
        if len(sys.argv) < 3:
            print("\n  Usage:  python test_model.py  --remove  <image_path>\n")
        else:
            remove_correction(sys.argv[2])

    else:
        classify_image(sys.argv[1])
