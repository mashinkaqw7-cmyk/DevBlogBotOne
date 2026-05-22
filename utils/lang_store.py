# utils/lang_store.py
import json
import os
from typing import Optional

BASE_DIR = os.path.dirname(os.path.dirname(__file__)) if os.path.dirname(__file__) else "."
STORE_PATH = os.path.join(BASE_DIR, "user_langs.json")

def _load_store() -> dict:
    try:
        with open(STORE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except Exception:
        return {}

def _save_store(data: dict):
    try:
        with open(STORE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def save_user_lang(user_id: int, lang_code: str):
    data = _load_store()
    data[str(user_id)] = {"lang": lang_code}
    _save_store(data)

def load_user_lang(user_id: int) -> Optional[str]:
    data = _load_store()
    entry = data.get(str(user_id))
    if entry and isinstance(entry, dict):
        return entry.get("lang")
    return None

def delete_user_lang(user_id: int):
    data = _load_store()
    if str(user_id) in data:
        del data[str(user_id)]
        _save_store(data)
