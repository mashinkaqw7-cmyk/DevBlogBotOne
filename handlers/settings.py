# handlers/settings.py
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from telegram.ext import CallbackQueryHandler, CommandHandler
from i18n import t
from keyboards import main_menu_keyboard

KEY_PREFS = "prefs"

DEFAULT_PREFS = {
    "theme": "auto",  # auto / light / dark
    "quick_buttons": ["menu.rates", "menu.converter", "menu.news"],
}

def _get_prefs(context):
    prefs = context.user_data.get(KEY_PREFS)
    if not prefs:
        prefs = DEFAULT_PREFS.copy()
        context.user_data[KEY_PREFS] = prefs
    return prefs

def _theme_label(theme, lang):
    mapping = {
        "auto": {"ru": "Авто", "en": "Auto"},
        "light": {"ru": "Светлая", "en": "Light"},
        "dark": {"ru": "Тёмная", "en": "Dark"},
    }
    return mapping.get(theme, {}).get(lang, theme)

def _build_settings_keyboard(context):
    prefs = _get_prefs(context)
    lang = context.user_data.get("lang", "ru")
    theme_label = _theme_label(prefs.get("theme", "auto"), lang)

    kb = [
        [InlineKeyboardButton(f"{t(context, 'settings.theme')}: {theme_label}", callback_data="set:theme")],
        [InlineKeyboardButton(t(context, "settings.reset_quick"), callback_data="action:reset_quick")],
        [InlineKeyboardButton(t(context, "settings.language.menu_back"), callback_data="settings:back")]
    ]
    return InlineKeyboardMarkup(kb)

async def settings_menu(update: Update, context):
    message = update.message or (update.callback_query and update.callback_query.message)
    if not message:
        return
    prefs = _get_prefs(context)
    lang = context.user_data.get("lang", "ru")
    theme_label = _theme_label(prefs.get("theme", "auto"), lang)
    quick = prefs.get("quick_buttons", [])
    quick_labels = ", ".join([t({'user_data': {'lang': lang}}, k) for k in quick]) if quick else t(context, "settings.quick_none")

    text = (
        f"{t(context, 'settings.language.title')}\n\n"
        f"{t(context, 'settings.current_values')}\n\n"
        f"{t(context, 'settings.theme')}: {theme_label}\n"
        f"{t(context, 'settings.quick_selected')}: {quick_labels}"
    )
    await message.reply_text(text, reply_markup=_build_settings_keyboard(context))

async def settings_callback(update: Update, context):
    query = update.callback_query
    if not query:
        return
    await query.answer()
    data = query.data or ""
    prefs = _get_prefs(context)

    # Cycle theme: auto -> light -> dark -> auto
    if data == "set:theme":
        order = ["auto", "light", "dark"]
        cur = prefs.get("theme", "auto")
        nxt = order[(order.index(cur) + 1) % len(order)] if cur in order else "auto"
        prefs["theme"] = nxt
        await query.edit_message_text(t(context, "settings.updated"), reply_markup=_build_settings_keyboard(context))
        return

    # Reset quick buttons to default
    if data == "action:reset_quick":
        prefs["quick_buttons"] = DEFAULT_PREFS["quick_buttons"].copy()
        await query.edit_message_text(t(context, "settings.quick_reset_done"), reply_markup=_build_settings_keyboard(context))
        return

    # Back: re-show settings
    if data == "settings:back":
        try:
            await query.edit_message_text(t(context, "settings.language.title"), reply_markup=_build_settings_keyboard(context))
        except Exception:
            await query.message.reply_text(t(context, "settings.language.title"), reply_markup=_build_settings_keyboard(context))
        return

def register(app):
    app.add_handler(CommandHandler("settings", settings_menu))
    app.add_handler(CallbackQueryHandler(settings_callback, pattern=r"^(set:|action:|settings:)"))
