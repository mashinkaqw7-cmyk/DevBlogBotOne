# handlers/start.py
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from telegram.ext import ContextTypes
from i18n import t
from handlers.settings_language import LANGUAGES
from keyboards import main_menu_keyboard

# /start — выбор языка
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("Русский 🇷🇺", callback_data="lang_ru"),
            InlineKeyboardButton("English 🇬🇧", callback_data="lang_en"),
        ]
    ]

    await update.message.reply_text(
        t(context, "start.choose_language"),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# Callback выбора языка
async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "lang_ru":
        context.user_data["lang"] = "ru"
        name = "Русский 🇷🇺"
    else:
        context.user_data["lang"] = "en"
        name = "English 🇬🇧"

    await query.edit_message_text(t(context, "settings.language.saved", name=name))

    try:
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=t(context, "menu.header"),
            reply_markup=main_menu_keyboard(context)
        )
    except Exception:
        kb = [
            [KeyboardButton(t(context, "menu.rates")), KeyboardButton(t(context, "menu.news"))],
            [KeyboardButton(t(context, "menu.converter")), KeyboardButton(t(context, "menu.about"))],
            [KeyboardButton(t(context, "menu.settings"))],
        ]
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=t(context, "menu.header"),
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
        )


# 🔄 Вернуться к выбору языка
async def return_to_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        t(context, "settings.language.back"),
        reply_markup=ReplyKeyboardRemove()
    )

    keyboard = [
        [
            InlineKeyboardButton("Русский 🇷🇺", callback_data="lang_ru"),
            InlineKeyboardButton("English 🇬🇧", callback_data="lang_en"),
        ]
    ]

    await update.message.reply_text(
        t(context, "start.choose_language"),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
