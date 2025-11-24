import torch
import timm
from PIL import Image
from torchvision import transforms as T
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler
import io, json
from openai import OpenAI

# ===================== CONFIG =====================
with open("config.json","r",encoding="utf-8") as f:
    CFG = json.load(f)

BOT_TOKEN  = CFG["telegram_bot_token"]
OPENAI_KEY = CFG["openai_api_key"]
ALLOWED_USERS = CFG["allowed_users"]
DEFAULT_LANG = CFG.get("default_language","uz-lat")
MODEL_PATH  = CFG.get("model_path","disease_model/model.pth")

# ===================== LANGUAGE PACK =====================
LANG = {
    "uz-lat": {
        "start": "Assalomu alaykum! Men Agro AI botman.\nRasm yuboring yoki savol bering.",
        "process": "⏳ Tahlil qilinmoqda, kuting...",
        "not_leaf": "❌ Bu rasm o‘simlik bargiga o‘xshamaydi. Iltimos, barg rasmini yuboring.",
        "disease": "Kasallik:",
        "conf": "Ishonchlilik:",
        "ask_follow": "Savolingiz bo‘lsa, yozib yuboring.",
        "bad_q": "❌ Savol faqat qishloq xo‘jaligi bo‘yicha bo‘lishi kerak."
    },
    "ru": {
        "start": "Здравствуйте! Отправьте фото листа растения или задайте вопрос.",
        "process": "⏳ Анализ изображения...",
        "not_leaf": "❌ Похоже, это не лист растения. Пришлите фото листа.",
        "disease": "Болезнь:",
        "conf": "Уверенность:",
        "ask_follow": "Если есть вопросы – напишите.",
        "bad_q": "❌ Вопрос должен относиться к сельскому хозяйству."
    }
}

# ===================== MODEL LOAD =====================
CLASSES = [
 'Apple___Apple_scab','Apple___Black_rot','Apple___Cedar_apple_rust','Apple___healthy',
 'Potato___Early_blight','Potato___Late_blight','Potato___healthy',
 'Tomato___Bacterial_spot','Tomato___Early_blight','Tomato___Late_blight',
 'Tomato___Leaf_Mold','Tomato___Septoria_leaf_spot',
 'Tomato___Spider_mites Two-spotted_spider_mite','Tomato___Target_Spot',
 'Tomato___Tomato_Yellow_Leaf_Curl_Virus','Tomato___Tomato_mosaic_virus',
 'Tomato___healthy'
]

model = timm.create_model("efficientnet_b3", pretrained=False, num_classes=len(CLASSES))
state = torch.load(MODEL_PATH, map_location="cpu", weights_only=True)
model.load_state_dict(state)
model.eval()

transform = T.Compose([
    T.Resize((224,224)), T.ToTensor(),
    T.Normalize([0.485,0.456,0.406],[0.229,0.224,0.225])
])

# ===================== OPENAI =====================
client = OpenAI(api_key=OPENAI_KEY)
USER_LANG = {}
LAST_DISEASE = {}  # stores last diagnosis per user

# ===================== LEAF VALIDATION =====================
import base64

async def is_leaf_image(img_bytes: bytes) -> bool:
    """Check with GPT if image contains a leaf or plant."""
    try:
        b64 = base64.b64encode(img_bytes).decode("utf-8")

        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a binary classifier. Only answer yes or no."},
                {"role": "user", "content": [
                    {"type": "text", "text": "Does this image contain a LEAF or a PLANT? Answer only yes or no."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
                ]}
            ],
            max_tokens=2,
        )

        answer = res.choices[0].message.content.strip().lower()
        return answer.startswith("y")  # yes == leaf/plant
    except Exception as e:
        print("Leaf check failed:", e)
        return True  # fallback: allow classification

# ===================== TREATMENT =====================
async def treatment(disease, lang):
    prompt = f"""
    Give treatment instructions for plant disease.
    Language: {lang}
    Format:
    Disease (English + local name)
    Cause:
    Treatment (organic + chemical):
    Max 80 words.
    Disease name: {disease}
    """
    r = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}]
    )
    return r.choices[0].message.content.strip()

# ===================== PREDICTION =====================
async def predict(img_bytes):
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    x = transform(img).unsqueeze(0)
    with torch.no_grad():
        y = model(x)
        idx = torch.argmax(y).item()
        conf = torch.softmax(y,dim=1)[0][idx].item()
    return CLASSES[idx], round(conf*100,2)

# ===================== HANDLERS =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    USER_LANG[uid] = DEFAULT_LANG
    await update.message.reply_text(LANG[DEFAULT_LANG]["start"])

async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = USER_LANG.get(uid, DEFAULT_LANG)
    if uid not in ALLOWED_USERS:
        return

    await update.message.reply_text(LANG[lang]["process"])
    file = await update.message.photo[-1].get_file()
    img_bytes = await file.download_as_bytearray()

    # Leaf validation
    valid = await is_leaf_image(img_bytes)
    if not valid:
        return await update.message.reply_text(LANG[lang]["not_leaf"])

    disease, conf = await predict(img_bytes)
    text = await treatment(disease, lang)

    LAST_DISEASE[uid] = {"disease": disease, "text": text}

    await update.message.reply_text(
        f"{LANG[lang]['disease']} {disease}\n"
        f"{LANG[lang]['conf']} {conf}%\n\n"
        f"{text}\n\n"
        f"{LANG[lang]['ask_follow']}"
    )

async def text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = USER_LANG.get(uid, DEFAULT_LANG)
    if uid not in ALLOWED_USERS:
        return

    q = update.message.text.lower()
    
    # Follow-up explanation
    if uid in LAST_DISEASE:
        prompt = f"Explain more simply in {lang}. User question: {q}\nPrevious info: {LAST_DISEASE[uid]['text']}"
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"user","content":prompt}]
        )
        return await update.message.reply_text(r.choices[0].message.content.strip())

    return await update.message.reply_text(LANG[lang]["bad_q"])

# ===================== RUN =====================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, photo))
    app.add_handler(MessageHandler(filters.TEXT, text))
    print("🤖 Agro AI bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
