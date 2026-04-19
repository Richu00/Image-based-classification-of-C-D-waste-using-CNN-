# ============================================================
#  C&D WASTE CLASSIFIER  –  TRAINING SCRIPT  (FIXED VERSION)
#  Classifies: Concrete, Glass, Metal, Plastic, Wood
#
#  WHAT WAS FIXED (compared to the previous version):
#  ─────────────────────────────────────────────────────────
#  FIX 1 → DATA AUGMENTATION added for training images
#           Randomly flips, rotates, changes brightness.
#           Forces the model to learn the material itself,
#           not just one specific angle or lighting.
#           → Directly fixes rock/concrete confusion.
#
#  FIX 2 → FINE-TUNING: last 3 backbone layers UNFROZEN
#           Previously ALL layers were frozen — too rigid.
#           Now the last 3 layers adapt to your specific
#           materials (concrete texture vs rock texture).
#
#  FIX 3 → LOWER LEARNING RATE (0.0001 instead of 0.001)
#           Required when fine-tuning backbone layers.
#           Prevents the model from forgetting ImageNet.
#
#  FIX 4 → MORE EPOCHS (15 instead of 5)
#           Fine-tuning needs more passes to settle.
#
#  FIX 5 → SAVES BEST MODEL AUTOMATICALLY
#           waste_classifier.pth always = best epoch result.
#
#  HOW TO USE:
#  1. pip install torch torchvision pillow
#  2. Organise dataset/ folder (same structure as before)
#  3. python train_model.py
#  4. waste_classifier.pth will be saved when done
# ============================================================

import torch
import torch.nn as nn
from torchvision import datasets, transforms, models
from torch.utils.data import DataLoader

# ── STEP 1: Settings ─────────────────────────────────────────
DATASET_PATH  = "dataset"
BATCH_SIZE    = 16
NUM_EPOCHS    = 15       # ← increased from 5  (fine-tuning needs more passes)
LEARNING_RATE = 0.0001   # ← lowered from 0.001 (IMPORTANT for fine-tuning)
NUM_CLASSES   = 5        # concrete, glass, metal, plastic, wood

# ── STEP 2: Image transforms ──────────────────────────────────
#
# FIX 1: TRAINING transform now includes AUGMENTATION.
#
# What is augmentation?
#   Every time the model sees an image, it is randomly changed
#   (flipped, rotated, brightened, darkened). The label stays
#   the same. A rotated photo of concrete is still concrete.
#   This means one image effectively becomes 20+ different images
#   across 15 epochs — without adding any files.
#
# Why does this fix concrete vs rock confusion?
#   If the model only ever saw concrete from one angle/lighting,
#   it learns that specific appearance, not the material itself.
#   Augmentation forces it to learn: "grey chunky rough broken
#   material = concrete" regardless of angle or brightness.
#
transform_train = transforms.Compose([
    transforms.Resize((256, 256)),         # Slightly bigger first
    transforms.RandomCrop(224),            # Random crop → different view each epoch
    transforms.RandomHorizontalFlip(),     # Flip left-right 50% of the time
    transforms.RandomVerticalFlip(p=0.2), # Flip upside-down 20% of the time
    transforms.RandomRotation(20),         # Rotate up to ±20 degrees randomly
    transforms.ColorJitter(
        brightness=0.3,                    # Vary brightness (simulates different lighting)
        contrast=0.3,                      # Vary contrast
        saturation=0.2,                    # Slight colour variation
        hue=0.05                           # Tiny hue shift (keeps colours realistic)
    ),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std =[0.229, 0.224, 0.225]
    )
])

# VALIDATION transform — NO augmentation at all.
# We never augment validation images. Clean images = fair test.
transform_val = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std =[0.229, 0.224, 0.225]
    )
])

# ── STEP 3: Load images from disk ────────────────────────────
# Note: training uses transform_train (with augmentation)
#       validation uses transform_val  (without augmentation)
train_data = datasets.ImageFolder(DATASET_PATH + "/train", transform=transform_train)
val_data   = datasets.ImageFolder(DATASET_PATH + "/val",   transform=transform_val)

train_loader = DataLoader(train_data, batch_size=BATCH_SIZE, shuffle=True)
val_loader   = DataLoader(val_data,   batch_size=BATCH_SIZE, shuffle=False)

print("Classes found:", train_data.classes)
print("Training images :", len(train_data))
print("Validation images:", len(val_data))

# ── STEP 4: Build the model with FINE-TUNING ─────────────────
#
# FIX 2: Unfreeze the last 3 backbone layers.
#
# Why this matters:
#   The MobileNetV2 backbone has 19 feature layers (0 to 18).
#   The later layers detect the most specific features —
#   exact textures, surface details, material appearance.
#   By unfreezing layers 16, 17, 18 we let the model say:
#   "I already know general shapes and edges from ImageNet,
#    but now I'll also learn what C&D concrete looks like."
#
# This is the main fix for concrete vs rock confusion.
#
model = models.mobilenet_v2(weights="IMAGENET1K_V1")

# First freeze everything (same as before)
for param in model.parameters():
    param.requires_grad = False

# Then unfreeze only the last 3 feature layers
# model.features is a list: [layer0, layer1, ..., layer18]
# model.features[-3:] = [layer16, layer17, layer18]
for param in model.features[-3:].parameters():
    param.requires_grad = True   # These 3 layers WILL be updated during training

# Replace the final output layer (same as before)
model.classifier[1] = nn.Linear(
    in_features  = model.classifier[1].in_features,
    out_features = NUM_CLASSES
)
# The new classifier layer is also trainable by default

# ── STEP 5: Loss function and optimiser ──────────────────────
loss_function = nn.CrossEntropyLoss()

# FIX 3: Pass ALL trainable parameters to the optimiser.
# Previously we only passed model.classifier[1].parameters()
# because everything else was frozen.
# Now we have 3 unfrozen backbone layers too, so we collect
# ALL parameters where requires_grad=True.
optimizer = torch.optim.Adam(
    filter(lambda p: p.requires_grad, model.parameters()),
    lr=LEARNING_RATE   # 0.0001 — small steps to protect ImageNet knowledge
)

# ── STEP 6: Train ────────────────────────────────────────────
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model  = model.to(device)
print("\nUsing device:", device)
print(f"Training for {NUM_EPOCHS} epochs  |  lr={LEARNING_RATE}")
print("Fine-tuning: last 3 backbone layers + classifier head\n")

best_accuracy = 0.0   # We will track the best epoch

for epoch in range(NUM_EPOCHS):
    model.train()
    total_loss = 0

    for images, labels in train_loader:
        images = images.to(device)
        labels = labels.to(device)

        predictions = model(images)
        loss = loss_function(predictions, labels)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        total_loss += loss.item()

    # ── Validation ───────────────────────────────────────────
    model.eval()
    correct = 0
    total   = 0

    with torch.no_grad():
        for images, labels in val_loader:
            images = images.to(device)
            labels = labels.to(device)
            predictions  = model(images)
            _, predicted = torch.max(predictions, 1)
            total   += labels.size(0)
            correct += (predicted == labels).sum().item()

    accuracy = 100 * correct / total
    avg_loss = total_loss / len(train_loader)
    print(f"Epoch {epoch+1:>2}/{NUM_EPOCHS}  |  Loss: {avg_loss:.3f}  |  Val Accuracy: {accuracy:.1f}%", end="")

    # FIX 5: Save ONLY when accuracy improves.
    # This means the saved file is ALWAYS the best result,
    # even if accuracy dips in later epochs.
    if accuracy > best_accuracy:
        best_accuracy = accuracy
        torch.save(model.state_dict(), "waste_classifier.pth")
        print("  ← NEW BEST — saved")
    else:
        print()

# ── STEP 7: Done ─────────────────────────────────────────────
print(f"\nBest validation accuracy achieved: {best_accuracy:.1f}%")
print("Model saved as  waste_classifier.pth")
print("Done! You can now run  test_model.py  to classify new images.")
print()
print("── HARD NEGATIVE TRAINING (FIX 4) ──────────────────────")
print("If the model still gets certain images wrong:")
print("  1. Copy the wrongly classified image into the")
print("     CORRECT class folder:  dataset/train/concrete/")
print("  2. Run  python train_model.py  again")
print("  3. Repeat for each type of image it keeps getting wrong")
print("─────────────────────────────────────────────────────────")
