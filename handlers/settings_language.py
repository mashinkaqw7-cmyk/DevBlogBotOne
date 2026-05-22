# handlers/settings_language.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler
from i18n import t
from keyboards import main_menu_keyboard

LANGUAGES = [
    ("ru", "Русский"),
    ("en", "English"),
]

LANG_KEY = "lang"

def _build_lang_keyboard(context, selected: str | None = None):
    buttons = []
    row = []
    for code, name in LANGUAGES:
        label = f"{name} {'✅' if selected == code else ''}"
        row.append(InlineKeyboardButton(label, callback_data=f"lang:set:{code}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([
        InlineKeyboardButton(t(context, "settings.language.menu_back"), callback_data="lang:back")
    ])
    return InlineKeyboardMarkup(buttons)

async def settings_language_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message or (update.callback_query and update.callback_query.message)
    if not message:
        return
    current = context.user_data.get(LANG_KEY, "ru")
    await message.reply_text(t(context, "settings.language.title"), reply_markup=_build_lang_keyboard(context, selected=current))

async def lang_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    await query.answer()
    data = query.data or ""

    if data.startswith("lang:set:"):
        code = data.split(":", 2)[2]
        context.user_data[LANG_KEY] = code
        name = next((n for c, n in LANGUAGES if c == code), code)
        try:
            await query.edit_message_text(t(context, "settings.language.saved", name=name), reply_markup=_build_lang_keyboard(context, selected=code))
        except Exception:
            await query.message.reply_text(t(context, "settings.language.saved", name=name), reply_markup=_build_lang_keyboard(context, selected=code))

        # Отправляем главное меню как reply-клавиатуру
        try:
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=t(context, "menu.header"),
                reply_markup=main_menu_keyboard(context)
            )
        except Exception:
            pass
        return

    if data == "lang:back":
        current = context.user_data.get(LANG_KEY, "ru")
        try:
            await query.edit_message_text(t(context, "settings.language.title"), reply_markup=_build_lang_keyboard(context, selected=current))
        except Exception:
            await query.message.reply_text(t(context, "settings.language.title"), reply_markup=_build_lang_keyboard(context, selected=current))
        return

def register(app):
    app.add_handler(CommandHandler("settings_language", settings_language_menu))
    app.add_handler(CallbackQueryHandler(lang_callback_handler, pattern=r"^lang:"))
