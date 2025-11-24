import os
import json
import asyncio
from datetime import datetime

from aiogram import Bot, Dispatcher, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.types import (
    Message,
    KeyboardButton,
    ReplyKeyboardMarkup
)
from aiogram.filters import CommandStart

# Core modules
from core.language_manager import get_user_lang, set_user_lang, t as tr
from core.user_manager import save_user, save_user_location, save_user_report
from core.weather import get_weather, render_weather
from core.gpt_client import (
    gpt_clean_text,
    gpt_predict_disease,
    gpt_crop_match,
    gpt_yes_no,
    gpt_enrich_local_model,
    topic_guard
)
from core.predictor import predict_disease, MODEL_CLASSES


# ============================================================
# BOT INIT
# ============================================================
CFG = json.load(open("config.json"))
bot = Bot(
    token=CFG["telegram_bot_token"],
    default=DefaultBotProperties(parse_mode="HTML")
)
dp = Dispatcher()
rt = Router()
dp.include_router(rt)

USER_STATE = {}


# ============================================================
# KEYBOARDS
# ============================================================
def language_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🇺🇿 O‘zbek (Lotin)")],
            [KeyboardButton(text="Ўзбекча (Крилл)")],
            [KeyboardButton(text="🇷🇺 Русский")],
            [KeyboardButton(text="🇬🇧 English")]
        ],
        resize_keyboard=True
    )


def main_menu(lang):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=f"❓ {tr(lang, 'ask_question')}")],
            [KeyboardButton(text=f"📸 {tr(lang, 'send_photo')}")],
            [KeyboardButton(text=f"🌦 {tr(lang, 'weather')}")],
            [KeyboardButton(text=f"📍 {tr(lang, 'send_location_btn')}", request_location=True)],
            [KeyboardButton(text=f"🛠 {tr(lang, 'report')}")],
            [KeyboardButton(text=f"🌐 {tr(lang, 'change_language')}")]
        ],
        resize_keyboard=True
    )


def weather_days_keyboard(lang):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=f"5️⃣ {tr(lang, 'weather_5')}")],
            [KeyboardButton(text=f"🔟 {tr(lang, 'weather_10')}")],
            [KeyboardButton(text=f"1️⃣5️⃣ {tr(lang, 'weather_15')}")]
        ],
        resize_keyboard=True
    )


# ============================================================
# START COMMAND
# ============================================================
@rt.message(CommandStart())
async def start_cmd(msg: Message):
    user_id = str(msg.from_user.id)
    save_user(user_id)
    USER_STATE.pop(user_id, None)

    await msg.answer(
        "Tilni tanlang / Выберите язык / Choose language:",
        reply_markup=language_keyboard()
    )


# ============================================================
# LANGUAGE SELECTION
# ============================================================
LANG_MAP = {
    "🇺🇿 O‘zbek (Lotin)": "uz",
    "Ўзбекча (Крилл)": "uzc",
    "🇷🇺 Русский": "ru",
    "🇬🇧 English": "en",
}


@rt.message(F.text.in_(LANG_MAP.keys()))
async def choose_language(msg: Message):
    user_id = str(msg.from_user.id)
    lang = LANG_MAP[msg.text]

    set_user_lang(user_id, lang)
    USER_STATE.pop(user_id, None)

    await msg.answer(tr(lang, "welcome"), reply_markup=main_menu(lang))


# ============================================================
# CHANGE LANGUAGE BUTTON
# ============================================================
@rt.message(lambda m: m.text and tr(get_user_lang(str(m.from_user.id)), "change_language") in m.text)
async def change_language_btn(msg: Message):
    await msg.answer(
        "Tilni tanlang / Выберите язык / Choose language:",
        reply_markup=language_keyboard()
    )


# ============================================================
# SAVE LOCATION
# ============================================================
@rt.message(F.location)
async def save_location_handler(msg: Message):
    user_id = str(msg.from_user.id)
    lang = get_user_lang(user_id)

    save_user_location(user_id, msg.location.latitude, msg.location.longitude)

    await msg.answer(
        tr(lang, "location_saved"),
        reply_markup=main_menu(lang)
    )


# ============================================================
# MAIN MESSAGE ROUTER (TEXT)
# ============================================================
@rt.message(F.text)
async def menu_router(msg: Message):
    user_id = str(msg.from_user.id)
    lang = get_user_lang(user_id)
    text = msg.text.strip()

    # ----------------------------
    # WEATHER
    # ----------------------------
    if text.endswith(tr(lang, "weather")):
        USER_STATE[user_id] = {"weather": True}
        return await msg.answer(tr(lang, "weather_choose_days"), reply_markup=weather_days_keyboard(lang))

    # Weather day selection
    if USER_STATE.get(user_id, {}).get("weather"):
        if text.endswith(tr(lang, "weather_5")):
            days = 5
        elif text.endswith(tr(lang, "weather_10")):
            days = 10
        elif text.endswith(tr(lang, "weather_15")):
            days = 15
        else:
            return

        data = json.load(open(f"users/{user_id}/user.json"))
        loc = data.get("location")
        if not loc:
            USER_STATE.pop(user_id, None)
            return await msg.answer(tr(lang, "location_not_set"), reply_markup=main_menu(lang))

        weather = get_weather(loc["lat"], loc["lon"], days)
        if not weather:
            USER_STATE.pop(user_id, None)
            return await msg.answer(tr(lang, "weather_error"), reply_markup=main_menu(lang))

        forecast = render_weather(weather, days, lang)
        USER_STATE.pop(user_id, None)
        return await msg.answer(forecast, reply_markup=main_menu(lang))

    # ----------------------------
    # SEND PHOTO
    # ----------------------------
    if text.endswith(tr(lang, "send_photo")):
        USER_STATE[user_id] = {"awaiting_crop": True}
        return await msg.answer(tr(lang, "ask_crop_name_first"))

    # Crop name input
    if USER_STATE.get(user_id, {}).get("awaiting_crop"):
        match = await gpt_crop_match(text.lower(), MODEL_CLASSES)
        USER_STATE[user_id]["crop_name"] = match or text.lower()
        USER_STATE[user_id]["awaiting_crop"] = False
        return await msg.answer(tr(lang, "send_photo_now"))

    # ----------------------------
    # REPORT
    # ----------------------------
    if text.endswith(tr(lang, "report")):
        USER_STATE[user_id] = {"report": True}
        return await msg.answer(tr(lang, "report_prompt"))

    if USER_STATE.get(user_id, {}).get("report"):
        save_user_report(user_id, text)
        USER_STATE.pop(user_id, None)
        return await msg.answer(tr(lang, "report_success"), reply_markup=main_menu(lang))

    # ----------------------------
    # ASK QUESTION
    # ----------------------------
    if text.endswith(tr(lang, "ask_question")):
        return await msg.answer(tr(lang, "ask_question_prompt"))

    # ----------------------------
    # TOPIC GUARD (Important)
    # ----------------------------
    is_agro = await topic_guard(text)
    if not is_agro:
        return await msg.answer(tr(lang, "topic_not_agriculture"))

    # ----------------------------
    # DEFAULT GPT TEXT ANSWER
    # ----------------------------
    resp = await gpt_clean_text(text, lang)
    return await msg.answer(resp)


# ============================================================
# PHOTO HANDLER
# ============================================================
@rt.message(F.photo)
async def photo_handler(msg: Message):
    user_id = str(msg.from_user.id)
    lang = get_user_lang(user_id)

    if "crop_name" not in USER_STATE.get(user_id, {}):
        return await msg.answer(tr(lang, "please_first_type_crop"))

    crop_name = USER_STATE[user_id]["crop_name"]

    await msg.answer(tr(lang, "photo_analyzing"))

    # Download image
    file_id = msg.photo[-1].file_id
    file = await bot.get_file(file_id)
    img_data = (await bot.download_file(file.file_path)).read()

    # Check if plant
    ok = await gpt_yes_no(tr(lang, "leaf_prompt"), img_data)
    if ok != "YES":
        USER_STATE.pop(user_id, None)
        return await msg.answer(tr(lang, "not_leaf"))

    # Local model
    if crop_name in MODEL_CLASSES:
        pred = await predict_disease(img_data)
        enriched = await gpt_enrich_local_model(
            pred["disease"], pred["crop"], pred["confidence"], lang
        )
        USER_STATE.pop(user_id, None)
        return await msg.answer(enriched)

    # GPT Vision fallback
    result = await gpt_predict_disease(img_data, crop_name, lang)
    cleaned = await gpt_clean_text(result, lang)

    USER_STATE.pop(user_id, None)
    await msg.answer(cleaned)


# ============================================================
# RUN BOT
# ============================================================
async def run_bot():
    print("AgroYordamchi is running...")
    await dp.start_polling(bot)
