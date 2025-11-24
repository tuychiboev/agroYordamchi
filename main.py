import json
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, MessageHandler,
    CommandHandler, ContextTypes, filters
)

from openai import OpenAI

from modules.languages import *
from modules.leafcheck import leaf_present
from modules.disease import predict, treatment_text
from modules.qa import ask
from modules.weather import get_weather
from modules.admin import is_admin, broadcast_start, broadcast_collect, broadcast_done


# ==== CONFIG ====
with open("config.json","r",encoding="utf-8") as f:
    CFG = json.load(f)

BOT = CFG["telegram_bot_token"]
OPENAI_KEY = CFG["openai_api_key"]
WEATHER_KEY = CFG["tomorrow_api_key"]
ALLOWED = CFG["allowed_users"]

client = OpenAI(api_key=OPENAI_KEY)
admin_mode = {}


# ==== COMMANDS ====

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in ALLOWED:
        return await update.message.reply_text("❌ Access denied")

    await update.message.reply_text(
        "🌿 AgroAI — Plant Disease Assistant",
        reply_markup=main_menu(uid)
    )


async def lang(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in ALLOWED: return
    if not ctx.args: return await update.message.reply_text("usage: /lang uz|uzc|ru|en")

    lg = ctx.args[0].lower()
    if lg not in LANGS: return await update.message.reply_text("❌ unknown")

    user_lang[uid] = lg
    await update.message.reply_text(f"✔ Language set: {LANGS[lg]}", reply_markup=main_menu(uid))


async def weather(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in ALLOWED: return
    if not ctx.args: return await update.message.reply_text("usage: /weather city")

    res = await get_weather(WEATHER_KEY, " ".join(ctx.args), uid)
    await update.message.reply_text(res)


# ==== IMAGE ====

async def img(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in ALLOWED: return

    file = await update.message.photo[-1].get_file()
    img_bytes = await file.download_as_bytearray()

    await update.message.reply_text("🔍 Checking leaf...")

    if not await leaf_present(client, img_bytes):
        return await update.message.reply_text("❌ No leaf detected")

    await update.message.reply_text("⏳ Diagnosing...")

    d, c = await predict(img_bytes)
    lang = user_lang.get(uid, DEFAULT_LANG)
    txt = await treatment_text(client, d, lang)

    await update.message.reply_text(
        f"🌿 Disease: {d}\n📊 Confidence: {c}%\n\n💊 {txt}"
    )


# ==== TEXT / QA / ADMIN ====

async def text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in ALLOWED:
        return await update.message.reply_text("❌ Access denied")

    msg = update.message.text

    if uid in admin_mode and admin_mode[uid]:
        if msg == "/send":
            out = broadcast_done()
            for u in ALLOWED:
                try:
                    await ctx.bot.send_message(chat_id=u, text=out)
                except:
                    pass
            admin_mode.pop(uid)
            return await update.message.reply_text("✔ Broadcast sent.")
        else:
            await broadcast_collect(uid, msg)
            return await update.message.reply_text("➕ Saved")

    ans = await ask(client, msg, user_lang.get(uid, DEFAULT_LANG))
    await update.message.reply_text(ans)


async def admin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_admin(uid, CFG):
        return await update.message.reply_text("❌ Admin only")

    admin_mode[uid] = True
    await broadcast_start(uid, update)


# ==== RUN ====

def main():
    app = ApplicationBuilder().token(BOT).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("lang", lang))
    app.add_handler(CommandHandler("weather", weather))
    app.add_handler(CommandHandler("admin", admin))

    app.add_handler(MessageHandler(filters.PHOTO, img))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text))

    print("🤖 AgroAI running...")
    app.run_polling()


if __name__ == "__main__":
    main()
