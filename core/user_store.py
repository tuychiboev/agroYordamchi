import json
import os

BASE = "users"

if not os.path.exists(BASE):
    os.makedirs(BASE)

def user_file(uid):
    return os.path.join(BASE, f"{uid}.json")

def load_user(uid):
    path = user_file(uid)
    if not os.path.exists(path):
        return {"id": uid, "lang": "en"}  # default
    return json.load(open(path, "r", encoding="utf-8"))

def save_user(uid, data):
    path = user_file(uid)
    json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
