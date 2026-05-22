# main.py
import logging
import asyncio
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from telegram.request import HTTPXRequest

from config import TOKEN
from i18n import TRANSLATIONS, t

from handlers.start import start_command, language_callback, return_to_language
from handlers.menu import menu_command
from handlers.rates import rates_command
from handlers.news import news_command
from handlers.about import about_command
from handlers.converter import converter_command, convert_currency

# Логи
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

request = HTTPXRequest(
    connect_timeout=30,
    read_timeout=30,
)


async def text_router(update, context):
    """
    Универсальный маршрутизатор текста.
    Если включён режим конвертера (context.user_data['converter_mode']),
    и пользователь нажал другую кнопку/ввел текст, который маршрутизируется
    в НЕ-конвертерный обработчик, то мы автоматически выключаем режим конвертера,
    чтобы convert_currency не реагировал на этот ввод.
    """
    text = (update.message.text or "").strip()
    if not text:
        return

    routes = [
        ("menu.rates", rates_command),
        ("menu.news", news_command),
        ("menu.converter", converter_command),
        ("menu.about", about_command),
        ("menu.return_language", return_to_language),
    ]

    # проверяем только ru и en (TRANSLATIONS содержит только эти)
    for lang_code in TRANSLATIONS.keys():
        ctx = {"user_data": {"lang": lang_code}}
        for key, handler in routes:
            label = t(ctx, key)
            if text == label:
                try:
                    # Если режим конвертера включён, но пользователь выбрал НЕ конвертер,
                    # выключаем режим, чтобы convert_currency не сработал на это сообщение.
                    if context.user_data.get("converter_mode") and handler is not convert_currency and handler is not converter_command:
                        context.user_data.pop("converter_mode", None)
                        context.user_data.pop("converter_mode_ts", None)
                        context.user_data.pop("converter_ignore_mid", None)

                    await handler(update, context)
                except Exception as e:
                    logger.exception("Error while routing to handler %s: %s", handler, e)
                return
    return


def main():
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    app = (
        Application.builder()
        .token(TOKEN)
        .request(request)
        .concurrent_updates(True)
        .build()
    )

    # Callback для выбора языка (из start)
    app.add_handler(CallbackQueryHandler(language_callback, pattern=r"^lang_"))

    # Универсальный текстовый маршрутизатор (должен стоять до общего конвертера)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router), group=0)

    # Текстовые кнопки возврата языка (резерв)
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex(r"^🔄 Вернуться к выбору языка$"),
        return_to_language
    ))
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex(r"^🔄 Return to language selection$"),
        return_to_language
    ))

    # О боте (резервные обработчики)
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex(r"^ℹ️ О боте$"),
        about_command
    ))
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex(r"^ℹ️ About bot$"),
        about_command
    ))

    # Курсы валют (резерв)
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex(r"^📊 Курсы валют$"),
        rates_command
    ))
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex(r"^📊 Exchange rates$"),
        rates_command
    ))

    # Новости (резерв)
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex(r"^📰 Новости$"),
        news_command
    ))
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex(r"^📰 News$"),
        news_command
    ))

    # Конвертация (резерв)
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex(r"^💸 Конвертация валют$"),
        converter_command
    ))
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex(r"^💸 Currency converter$"),
        converter_command
    ))

    # Старт / меню (команды)
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("menu", menu_command))

    # Общий хендлер для конвертера (в самом конце) — автораспознавание конвертационных сообщений
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, convert_currency), group=10)

    print("Bot started...")
    app.run_polling()


if __name__ == "__main__":
    main()
