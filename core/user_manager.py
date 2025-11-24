import os
import json
from datetime import datetime


# ============================================================
# INTERNAL HELPERS
# ============================================================
def _user_dir(user_id: str) -> str:
    """Return directory path for user."""
    return os.path.join("users", user_id)


def _user_file(user_id: str) -> str:
    """Return user.json file path."""
    return os.path.join("users", user_id, "user.json")


def _load_user(user_id: str) -> dict:
    """
    Safely load user.json.
    Return {} if file does not exist OR JSON is invalid.
    """
    file = _user_file(user_id)

    if not os.path.exists(file):
        return {}

    try:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}  # corrupted or unreadable JSON


def _save_user(user_id: str, data: dict):
    """Safely save user.json, create directory if missing."""
    os.makedirs(_user_dir(user_id), exist_ok=True)

    with open(_user_file(user_id), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ============================================================
# BASIC USER CREATION
# ============================================================
def save_user(user_id: str):
    """
    Initialize user.json if missing.
    Do not overwrite existing settings.
    """
    data = _load_user(user_id)

    # Ensure at least language exists
    if "lang" not in data:
        data["lang"] = "en"

    _save_user(user_id, data)


# ============================================================
# LANGUAGE MANAGEMENT
# ============================================================
def get_user_lang(user_id: str) -> str:
    """Returns user language or 'en'."""
    data = _load_user(user_id)
    return data.get("lang", "en")


def set_user_lang(user_id: str, lang: str):
    """Save language to user.json."""
    data = _load_user(user_id)
    data["lang"] = lang
    _save_user(user_id, data)


# ============================================================
# LOCATION MANAGEMENT
# ============================================================
def save_user_location(user_id: str, lat: float, lon: float):
    """Store location inside user.json."""
    data = _load_user(user_id)
    data["location"] = {"lat": float(lat), "lon": float(lon)}
    _save_user(user_id, data)


def get_user_location(user_id: str):
    """Return location dict or None."""
    data = _load_user(user_id)
    loc = data.get("location")
    if isinstance(loc, dict) and "lat" in loc and "lon" in loc:
        return loc
    return None


# ============================================================
# REPORT HANDLING
# ============================================================
def save_user_report(user_id: str, text: str) -> str:
    """
    Save user-submitted report.
    Return saved file path.
    """
    report_dir = os.path.join("users", user_id, "reports")
    os.makedirs(report_dir, exist_ok=True)

    filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    path = os.path.join(report_dir, filename)

    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

    return path


def get_all_reports(user_id: str):
    """Return a sorted list of all report filenames."""
    report_dir = os.path.join("users", user_id, "reports")
    if not os.path.exists(report_dir):
        return []
    return sorted(os.listdir(report_dir))
