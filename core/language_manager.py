import json
import os

# Path to translations.json
LANG_PATH = os.path.join(os.path.dirname(__file__), "translations.json")

# Load translations into memory
with open(LANG_PATH, "r", encoding="utf-8") as f:
    TRANSLATIONS = json.load(f)


# ============================================================
# USER LANGUAGE MANAGEMENT
# ============================================================

def _user_file(user_id: str):
    return f"users/{user_id}/user.json"


def get_user_lang(user_id: str) -> str:
    """Returns user's language or English as default."""
    file = _user_file(user_id)

    if not os.path.exists(file):
        return "en"

    try:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("lang", "en")
    except:
        return "en"


def set_user_lang(user_id: str, lang: str):
    """Saves user's selected language."""
    os.makedirs(f"users/{user_id}", exist_ok=True)
    file = _user_file(user_id)

    data = {}
    if os.path.exists(file):
        try:
            data = json.load(open(file, "r", encoding="utf-8"))
        except:
            data = {}

    data["lang"] = lang

    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ============================================================
# TRANSLATION HANDLING
# ============================================================

def translate_ui(lang: str) -> dict:
    """Returns translation dict or English fallback."""
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"])


def t(lang: str, key: str) -> str:
    """
    Safe translation function:
    - Return translation in selected language
    - Otherwise return English
    - If missing, return key itself
    """
    lang_dict = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    return lang_dict.get(key, TRANSLATIONS["en"].get(key, key))
