import os
import json
import base64
from openai import AsyncOpenAI

# ============================================================
# Load API Key
# ============================================================
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.json")
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)

OPENAI_KEY = config.get("openai_api_key")
if not OPENAI_KEY:
    raise Exception("openai_api_key missing in config.json")

client = AsyncOpenAI(api_key=OPENAI_KEY)


# ============================================================
# Language Map (used for instruction language)
# ============================================================
LANG_MAP = {
    "uz": "Uzbek (Latin)",
    "uzc": "Uzbek (Cyrillic)",
    "ru": "Russian",
    "en": "English"
}

# ============================================================
# Multilingual field names for disease reports
# ============================================================
FIELD = {
    "uz": {
        "disease": "Kasallik",
        "crop": "O‘simlik",
        "confidence": "Ishonchlilik",
        "symptoms": "Belgilar",
        "treatment": "Davolash",
        "prevention": "Oldini olish",
        "causes": "Sabablar"
    },
    "uzc": {
        "disease": "Касаллик",
        "crop": "Ўсимлик",
        "confidence": "Ишончллик",
        "symptoms": "Белгилар",
        "treatment": "Даволаш",
        "prevention": "Олдини олиш",
        "causes": "Сабаблар"
    },
    "ru": {
        "disease": "Болезнь",
        "crop": "Растение",
        "confidence": "Уверенность",
        "symptoms": "Симптомы",
        "treatment": "Лечение",
        "prevention": "Профилактика",
        "causes": "Причины"
    },
    "en": {
        "disease": "Disease",
        "crop": "Crop",
        "confidence": "Confidence",
        "symptoms": "Symptoms",
        "treatment": "Treatment",
        "prevention": "Prevention",
        "causes": "Causes"
    }
}


# ============================================================
# Helper: Encode Image
# ============================================================
def encode_image(img_bytes: bytes) -> str:
    return base64.b64encode(img_bytes).decode("utf-8")


# ============================================================
# 0. Topic Guard
# ============================================================
async def topic_guard(question: str) -> bool:
    """
    Detect if question is agriculture-related.
    """
    prompt = f"""
    Determine if the question below is related to AGRICULTURE:
    - crops, plants, soil, irrigation
    - diseases, pests, fertilizers, pesticides
    - weather for farming
    - farming techniques

    Respond ONLY with "YES" or "NO".

    Question: {question}
    """

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    ans = response.choices[0].message.content.strip().upper()
    return "YES" in ans


# ============================================================
# 1. Clean Chat Answer
# ============================================================
async def gpt_clean_text(text: str, lang: str = "en"):
    target_lang = LANG_MAP.get(lang, "English")

    system_prompt = (
        f"You rewrite the user's text cleanly and clearly in {target_lang}. "
        "Keep it short. Keep agricultural context. No disclaimers."
    )

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ]
    )

    return response.choices[0].message.content.strip()


# ============================================================
# 2. Text Disease Explanation
# ============================================================
async def gpt_detect_disease(text: str, lang: str = "en"):
    target_lang = LANG_MAP.get(lang, "English")

    system_prompt = f"You are a crop disease expert. Respond briefly in {target_lang}."

    resp = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ]
    )

    return resp.choices[0].message.content.strip()


# ============================================================
# 3. GPT Vision Disease Detection (IMAGE)
# ============================================================
async def gpt_predict_disease(image_bytes: bytes, crop_type: str, lang: str):
    target_lang = LANG_MAP.get(lang, "English")
    F = FIELD[lang]  # multilingual labels
    img_b64 = encode_image(image_bytes)

    system_prompt = f"""
    You are an agricultural plant disease expert.

    IMPORTANT:
    - Respond ONLY in {target_lang}
    - Follow EXACT format below
    - Use FIELD LABEL translations provided

    FORMAT EXACTLY:

    🌿 {F['disease']}: <short name>

    🔍 {F['symptoms']}:
    - symptom 1
    - symptom 2
    - symptom 3

    🧪 {F['causes']}:
    - cause 1
    - cause 2

    💊 {F['treatment']}:
    - treatment 1
    - treatment 2
    - treatment 3

    🛡 {F['prevention']}:
    - prevention 1
    - prevention 2
    """

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}
                    },
                    {"type": "text", "text": f"Crop type: {crop_type}"}
                ]
            }
        ]
    )

    return response.choices[0].message.content.strip()


# ============================================================
# 4. YES / NO Image Detector
# ============================================================
async def gpt_yes_no(question: str, img_bytes: bytes):
    img_b64 = encode_image(img_bytes)

    resp = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}},
                    {"type": "text", "text": question}
                ]
            }
        ]
    )

    ans = resp.choices[0].message.content.strip().upper()

    # Accept YES in multiple languages
    YES_WORDS = ["YES", "ДА", "HA", "ҲА", "TRUE"]
    return "YES" if any(w in ans for w in YES_WORDS) else "NO"


# ============================================================
# 5. Crop Name Normalizer
# ============================================================
async def gpt_crop_match(user_crop: str, model_classes: list[str]):
    allowed = ", ".join(model_classes)

    system_prompt = f"""
    You normalize crop names.
    Allowed crops:
    {allowed}

    RULES:
    - User may type in any language
    - Fix spelling mistakes
    - Return EXACT match from allowed list
    - If no match → return NONE
    """

    resp = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_crop}
        ]
    )

    result = resp.choices[0].message.content.strip().lower()
    return result if result in model_classes else None


# ============================================================
# 6. Enrich Local PyTorch Model Output
# ============================================================
# ============================================================
# 6. Enrich Local Model Output (PyTorch model → GPT formatted)
# ============================================================
async def gpt_enrich_local_model(disease_name: str, crop: str, confidence: float, lang: str):
    target = LANG_MAP.get(lang, "English")

    system_prompt = (
        f"You are a crop disease expert. Respond only in {target}. "
        f"Format clearly using emojis. No disclaimers. Keep structure exactly."
    )

    prompt = f"""
    A local AI model detected:

    Crop: {crop}
    Disease: {disease_name}
    Confidence: {confidence}%

    Your tasks:
    - Provide a “common language explanation” (Xalq tilida) in 1–2 simple sentences
    - Write symptoms
    - Write treatment
    - Write prevention
    - Structure MUST be exactly as shown below
    - Translate everything into {target}

    REQUIRED FORMAT EXACTLY:

    🌿 Kasallik: {disease_name}
    🗣 Xalq tilida: <kasallikning oddiy tilda tushuntirishi>

    🌱 O‘simlik: {crop}
    📊 Ishonchlilik: {confidence}%

    🔍 Belgilar:
    - ...
    - ...
    - ...

    💊 Davolash:
    - ...
    - ...
    - ...

    🛡 Oldini olish:
    - ...
    """

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content.strip()
