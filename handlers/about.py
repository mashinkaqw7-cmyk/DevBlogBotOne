# handlers/about.py
from telegram import Update
from telegram.ext import ContextTypes
from i18n import t
import importlib

# Попытка получить конфигурацию (опционально)
try:
    import config
    BOT_VERSION = getattr(config, "BOT_VERSION", "0.0.1")
    CREATOR_HANDLE = getattr(config, "CREATOR_HANDLE", "@Anyxorr")
except Exception:
    BOT_VERSION = "0.0.1"
    CREATOR_HANDLE = "@Anyxorr"

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отправляет информацию о боте.
    Текст берётся из i18n через ключ 'about.text' и дополняется динамическими полями.
    """
    lang = context.user_data.get("lang", "ru")
    # Основной локализованный текст (в i18n должен быть ключ 'about.text')
    base = t(context, "about.text")

    # Дополнительные строки (локализованные)
    version_label = t(context, "about.version_label") if t(context, "about.version_label") != "about.version_label" else "Version"
    creator_label = t(context, "about.creator_label") if t(context, "about.creator_label") != "about.creator_label" else "Creator"

    # Собираем итоговый текст (HTML)
    text = (
        f"{base}\n\n"
        f"<b>{version_label}:</b> {BOT_VERSION}\n"
        f"<b>{creator_label}:</b> {CREATOR_HANDLE}"
    )

    # Отправляем как HTML (в i18n 'about.text' должен быть коротким описанием)
    await update.message.reply_text(text, parse_mode="HTML")
