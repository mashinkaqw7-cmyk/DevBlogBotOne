from typing import Dict

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "ru": {
        "start.choose_language": "Выберите язык / Choose language:",
        "start.already_selected": "Вы уже выбрали: {name}",
        "start.menu_hint": "Откройте меню или нажмите кнопку ниже, чтобы продолжить.",

        "menu.header": "Главное меню",
        "menu.rates": "📊 Курсы валют",
        "menu.news": "📰 Новости",
        "menu.converter": "💸 Конвертация валют",
        "menu.about": "ℹ️ О боте",
        "menu.settings": "⚙️ Настройки",
        "menu.return_language": "🔄 Вернуться к выбору языка",

        "converter.enabled": "Режим конвертера включён. Пример: 1 BTC в EUR или 1000 USD в RUB",
        "converter.no_amount": "❌ Не указана сумма. Пример: 100 USD в RUB",
        "converter.need_two": "❌ Укажите две валюты. Пример: 100 USD в RUB или 1 BTC в EUR",
        "converter.unknown_currency": "❌ Неизвестная валюта. Доступные: {codes}",
        "converter.timeout": "❌ Таймаут при запросе курсов. Попробуйте ещё раз.",
        "converter.error": "❌ Ошибка при получении курса. Попробуйте позже.",

        "rates.header": "Курс доллара (1 USD =)",
        "rates.updated": "Дата и время: {time}",

        "news.header": "Последние новости",
        "news.no_items": "Нет доступных новостей.",
        "news.loading": "Загружаю новости...",

        "about.text": "Я бот для курсов, новостей и конвертации валют.",

        "settings.language.saved": "Язык установлен: {name}",
        "settings.language.back": "Возврат к выбору языка",   # ← ДОБАВЛЕНО
    },

    "en": {
        "start.choose_language": "Choose language / Выберите язык:",
        "start.already_selected": "You already selected: {name}",
        "start.menu_hint": "Open the menu or press the button below to continue.",

        "menu.header": "Main menu",
        "menu.rates": "📊 Exchange rates",
        "menu.news": "📰 News",
        "menu.converter": "💸 Currency converter",
        "menu.about": "ℹ️ About bot",
        "menu.settings": "⚙️ Settings",
        "menu.return_language": "🔄 Return to language selection",

        "converter.enabled": "Converter mode enabled. Example: 1 BTC to EUR or 1000 USD to RUB",
        "converter.no_amount": "❌ No amount specified. Example: 100 USD to RUB",
        "converter.need_two": "❌ Specify two currencies. Example: 100 USD to RUB or 1 BTC to EUR",
        "converter.unknown_currency": "❌ Unknown currency. Supported: {codes}",
        "converter.timeout": "❌ Timeout while fetching rates. Try again.",
        "converter.error": "❌ Error fetching rate. Try later.",

        "rates.header": "USD exchange rate (1 USD =)",
        "rates.updated": "Date & Time: {time}",

        "news.header": "Latest news",
        "news.no_items": "No news available.",
        "news.loading": "Loading news...",

        "about.text": "I am a bot for rates, news and currency conversion.",

        "settings.language.saved": "Language set: {name}",
        "settings.language.back": "Returning to language selection",   # ← ДОБАВЛЕНО
    },
}


def t(context, key: str, **kwargs) -> str:
    """
    Возвращает перевод по ключу.
    Источник языка: context.user_data['lang'] -> fallback 'en' -> fallback 'ru'.
    Поддерживает context как объект с user_data, словарь {'user_data': {...}} или None.
    """
    lang = "ru"
    try:
        if context is None:
            lang = "ru"
        elif hasattr(context, "user_data"):
            ud = getattr(context, "user_data") or {}
            lang = ud.get("lang", lang)
        elif isinstance(context, dict):
            ud = context.get("user_data", {}) or {}
            lang = ud.get("lang", lang)
    except Exception:
        lang = "ru"

    d = TRANSLATIONS.get(lang, {})
    val = d.get(key)
    if val:
        return val.format(**kwargs) if kwargs else val

    val = TRANSLATIONS.get("en", {}).get(key)
    if val:
        return val.format(**kwargs) if kwargs else val

    val = TRANSLATIONS.get("ru", {}).get(key)
    if val:
        return val.format(**kwargs) if kwargs else val

    return key
