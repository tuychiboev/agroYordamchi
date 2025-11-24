import json
import logging
import base64
from io import BytesIO
from PIL import Image

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from openai import OpenAI

# Load config
with open("config.json", "r") as f:
    config = json.load(f)

TELEGRAM_BOT_TOKEN = config["telegram_bot_token"]
OPENAI_API_KEY = config["openai_api_key"]

client = OpenAI(api_key=OPENAI_API_KEY)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ===== OpenAI Models List =====
# You can edit this list anytime to test additional models
AI_MODELS = [
    ("gpt-4.1-mini", "Fast vision/explanation"),
    ("gpt-4.1", "Advanced vision diagnosis"),
    ("o1-mini", "General reasoning (no direct image support)"),
    ("o3-mini", "High-power reasoning (no direct image support)")
]


async def ask_model(model: str, desc: str, b64_image: str) -> str:
    """
    Calls a single OpenAI model and returns formatted output or error.
    """
    try:
        response = client.responses.create(
            model=model,
            input=[{
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": "Analyze this crop leaf image. Identify disease, cause, and treatment for a farmer."
                    },
                    {
                        "type": "input_image",
                        "image_url": f"data:image/jpeg;base64,{b64_image}"
                    }
                ]
            }]
        )
        answer = response.output_text
        return f"🟢 <b>{model}</b> ({desc})\n{answer}"

    except Exception as e:
        return f"🔴 <b>{model}</b> ({desc})\nError: {e}"


# ===== Telegram Bot Handlers =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌿 Send a clear leaf photo and I will analyze it using multiple AI models.\n"
        "The leaf should be visible and fill most of the image."
    )


async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        photo = update.message.photo[-1]
        file = await photo.get_file()
        img_bytes = await file.download_as_bytearray()

        # Convert image to Base64
        img = Image.open(BytesIO(img_bytes))
        buf = BytesIO()
        img.save(buf, format="JPEG")
        b64_img = base64.b64encode(buf.getvalue()).decode("utf-8")

        await update.message.reply_text("🧪 Analyzing leaf with multiple AI models…")

        # Run each model & send response separately
        for model, desc in AI_MODELS:
            result = await ask_model(model, desc, b64_img)

            # Ensure Telegram message length limit
            for i in range(0, len(result), 3800):
                await update.message.reply_text(result[i:i+3800], parse_mode="HTML")

    except Exception as e:
        logger.error(f"Image processing error: {e}")
        await update.message.reply_text("❗ Could not analyze the image. Please try again with a clearer leaf photo.")


# ===== Run Bot =====
def run():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_image))
    app.run_polling()


if __name__ == "__main__":
    run()
