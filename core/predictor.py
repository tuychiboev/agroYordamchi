import torch
import timm
from PIL import Image
from torchvision import transforms as T
import io, json, os

# Load config
with open("config.json", "r", encoding="utf-8") as f:
    CFG = json.load(f)

MODEL_PATH = CFG["model_path"]

# ----------------------------------------
# Crops supported by the trained model
# ----------------------------------------
MODEL_CLASSES = ["apple", "potato", "tomato"]

# ----------------------------------------
# All disease labels inside your model
# ----------------------------------------
CLASSES = [
    'Apple___Apple_scab','Apple___Black_rot','Apple___Cedar_apple_rust','Apple___healthy',
    'Potato___Early_blight','Potato___Late_blight','Potato___healthy',
    'Tomato___Bacterial_spot','Tomato___Early_blight','Tomato___Late_blight',
    'Tomato___Leaf_Mold','Tomato___Septoria_leaf_spot',
    'Tomato___Spider_mites Two-spotted_spider_mite','Tomato___Target_Spot',
    'Tomato___Tomato_Yellow_Leaf_Curl_Virus','Tomato___Tomato_mosaic_virus','Tomato___healthy'
]

# ----------------------------------------
# Load model
# ----------------------------------------
model = timm.create_model("efficientnet_b3", pretrained=False, num_classes=len(CLASSES))
state = torch.load(MODEL_PATH, map_location="cpu")
model.load_state_dict(state, strict=False)
model.eval()

# ----------------------------------------
# Image preprocessing
# ----------------------------------------
transform = T.Compose([
    T.Resize((224, 224)),
    T.ToTensor(),
    T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

# ----------------------------------------
# Helper to humanize label
# ----------------------------------------
def _parse_label(label: str):
    # Example: "Tomato___Early_blight"
    parts = label.split("___")
    crop = parts[0]
    disease = parts[1].replace("_", " ")

    return crop, disease.title()

# ----------------------------------------
# Prediction function
# ----------------------------------------
async def predict_disease(img_bytes):
    # Safe-loading image
    try:
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    except Exception:
        return {
            "crop": None,
            "disease": None,
            "confidence": 0,
            "raw": "Invalid or unreadable image."
        }

    x = transform(img).unsqueeze(0)

    with torch.no_grad():
        y = model(x)
        idx = torch.argmax(y).item()
        conf = torch.softmax(y, dim=1)[0][idx].item()

    raw_label = CLASSES[idx]
    crop, disease_name = _parse_label(raw_label)

    return {
        "crop": crop.lower(),
        "disease": disease_name,
        "confidence": round(conf * 100, 2),
        "raw": raw_label
    }
