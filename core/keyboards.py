from aiogram.utils.keyboard import ReplyKeyboardBuilder

def main_menu_kb(lang):
    kb = ReplyKeyboardBuilder()

    labels = {
        "uz_lat": ["Savol berish", "Kasallik aniqlash", "Ob-havo", "Xatolik haqida xabar"],
        "uz_cyr": ["Савол бериш", "Касаллик аниқлаш", "Об-ҳаво", "Хатолик ҳақида хабар"],
        "ru": ["Задать вопрос", "Определить болезнь", "Погода", "Сообщить об ошибке"],
        "en": ["Ask a question", "Detect disease", "Weather", "Report issue"]
    }

    for text in labels[lang]:
        kb.button(text=text)

    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)

def language_keyboard():
    kb = ReplyKeyboardBuilder()
    kb.button(text="O'zbek (Lotin)")
    kb.button(text="Ўзбек (Кирил)")
    kb.button(text="Русский")
    kb.button(text="English")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)
