# handlers/menu.py
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from i18n import t
from keyboards import main_menu_keyboard

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        kb = main_menu_keyboard(context)
        await update.message.reply_text(
            t(context, "menu.header"),
            reply_markup=kb
        )
    except Exception:
        kb = [
            [KeyboardButton(t(context, "menu.rates")), KeyboardButton(t(context, "menu.news"))],
            [KeyboardButton(t(context, "menu.converter")), KeyboardButton(t(context, "menu.about"))],
            [KeyboardButton(t(context, "menu.settings"))],
        ]
        await update.message.reply_text(
            t(context, "menu.header"),
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
        )
