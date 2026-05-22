# keyboards.py
from telegram import ReplyKeyboardMarkup
from i18n import t

def main_menu_keyboard(context_or_lang=None):
    """
    Возвращает ReplyKeyboardMarkup.
    context_or_lang может быть:
      - объект context (с user_data)
      - словарь {'user_data': {'lang': 'ru'}}
      - строка 'ru' / 'en'
      - None (по умолчанию 'ru')
    """
    lang = "ru"
    if isinstance(context_or_lang, str):
        lang = context_or_lang
    elif isinstance(context_or_lang, dict):
        ud = context_or_lang.get("user_data", {}) or {}
        lang = ud.get("lang", "ru")
    else:
        try:
            if context_or_lang and hasattr(context_or_lang, "user_data"):
                ud = getattr(context_or_lang, "user_data") or {}
                lang = ud.get("lang", "ru")
        except Exception:
            lang = "ru"

    kb = [
        [t({'user_data': {'lang': lang}}, "menu.converter"), t({'user_data': {'lang': lang}}, "menu.rates")],
        [t({'user_data': {'lang': lang}}, "menu.news"), t({'user_data': {'lang': lang}}, "menu.about")],
        [t({'user_data': {'lang': lang}}, "menu.return_language")],
    ]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)
