import datetime
import pytz
import aiohttp
import asyncio
import feedparser
from telegram import Update
from telegram.ext import ContextTypes

NEWS_API_KEY = "176b4a81991a4e36b405c7b42b0f870b"

# КЭШ
NEWS_CACHE = {
    "ru": {"time": None, "data": None},
    "en": {"time": None, "data": None}
}
CACHE_LIFETIME = 300  # 5 минут


# Полный список RSS (включая медленные)
RSS_RU = [
    "https://rssexport.rbc.ru/rbcnews/news/20/full.rss",
    "https://www.interfax.ru/rss.asp",
    "https://tass.ru/rss/v2.xml",
    "https://www.kommersant.ru/RSS/news.xml",
    "https://www.vedomosti.ru/rss/news",
    "https://www.banki.ru/xml/news.rss",
    "https://www.finmarket.ru/rss/main.asp",
    "https://ria.ru/export/rss2/economy/index.xml",
    "https://lenta.ru/rss/news/economics/"
]

RSS_EN = [
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.reutersagency.com/feed/?best-topics=business-finance",
    "https://www.cnbc.com/id/100727362/device/rss/rss.html"
]

# Ключевые слова
KEYWORDS_RU = [
    "доллар", "евро", "рубль", "нефть", "золото", "экономика",
    "ставка", "инфляция", "цб", "центробанк", "минфин",
    "рынок", "курс", "валют", "биржа", "торги", "финансы",
    "фондовый", "акции", "облигации", "санкции", "бюджет",
    "падение", "рост", "газ", "уголь", "сырь", "экспорт", "импорт"
]

KEYWORDS_EN = [
    "dollar", "euro", "oil", "gold", "economy", "inflation",
    "rate", "market", "stocks", "bonds", "finance", "export", "import"
]


# -----------------------------
# API NEWS
# -----------------------------
async def fetch_api_news(lang):
    if lang == "ru":
        query = "доллар евро экономика нефть золото рубль"
        lang_code = "ru"
    else:
        query = "currency economy dollar euro oil gold"
        lang_code = "en"

    url = (
        f"https://newsapi.org/v2/everything?"
        f"q={query}&language={lang_code}&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
    )

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 429:
                return None
            try:
                return await resp.json()
            except:
                return None


# -----------------------------
# PARALLEL RSS
# -----------------------------
async def fetch_single_rss(url):
    try:
        return feedparser.parse(url)
    except:
        return None


async def fetch_rss_news(lang):
    sources = RSS_RU if lang == "ru" else RSS_EN
    keywords = KEYWORDS_RU if lang == "ru" else KEYWORDS_EN

    # Параллельная загрузка всех RSS
    feeds = await asyncio.gather(*[fetch_single_rss(url) for url in sources])

    items = []
    for feed in feeds:
        if not feed:
            continue
        for entry in feed.entries[:20]:
            text = (entry.title + " " + entry.get("summary", "")).lower()
            if any(k in text for k in keywords):
                items.append(entry)

    return items[:10]  # больше новостей


# -----------------------------
# IMPACT ANALYSIS
# -----------------------------
def explain_impact(title, lang):
    title_low = title.lower()

    if any(w in title_low for w in ["ставка", "фрс", "цб", "rate", "fed"]):
        return "📈 Повышение ставок укрепляет валюту." if lang == "ru" else "📈 Rate hikes strengthen the currency."

    if any(w in title_low for w in ["нефть", "oil"]):
        return "🛢 Изменение цен на нефть влияет на рубль и доллар." if lang == "ru" else "🛢 Oil price changes affect USD and other currencies."

    if any(w in title_low for w in ["инфляция", "inflation"]):
        return "🔥 Рост инфляции ослабляет валюту." if lang == "ru" else "🔥 Rising inflation weakens the currency."

    return "💸 Новость влияет на мировые валютные рынки." if lang == "ru" else "💸 This affects global currency markets."


# -----------------------------
# BACKGROUND UPDATE
# -----------------------------
async def update_cache_in_background(lang):
    """Обновляет кэш в фоне, не блокируя пользователя."""
    print(f"[BACKGROUND] Обновляю кэш для языка: {lang}")

    now_ts = datetime.datetime.now().timestamp()

    # API
    api_data = await fetch_api_news(lang)

    if api_data and api_data.get("articles"):
        articles = api_data["articles"][:5]
        lines = []

        tz = pytz.timezone("Europe/Moscow" if lang == "ru" else "America/New_York")
        now = datetime.datetime.now(tz)

        header = (
            f"<b>Новости, влияющие на валюты</b>\n"
            f"<b>Дата:</b> {now.strftime('%d.%m.%Y %H:%M:%S')}\n\n"
            if lang == "ru"
            else
            f"<b>News affecting currencies</b>\n"
            f"<b>Date:</b> {now.strftime('%d.%m.%Y %H:%M:%S')}\n\n"
        )

        lines.append(header)

        for a in articles:
            title = a.get("title", "Без заголовка")
            source = a.get("source", {}).get("name", "")
            date = a.get("publishedAt", "")[:10]
            impact = explain_impact(title, lang)
            lines.append(f"• <b>{title}</b> ({source}, {date})\n{impact}\n")

        NEWS_CACHE[lang] = {"time": now_ts, "data": "\n".join(lines)}
        return

    # RSS fallback
    rss_items = await fetch_rss_news(lang)

    if not rss_items:
        NEWS_CACHE[lang] = {
            "time": now_ts,
            "data": "Нет новостей по валютам." if lang == "ru" else "No currency-related news."
        }
        return

    tz = pytz.timezone("Europe/Moscow" if lang == "ru" else "America/New_York")
    now = datetime.datetime.now(tz)

    header = (
        f"<b>Новости, влияющие на валюты</b>\n"
        f"<b>Дата:</b> {now.strftime('%d.%m.%Y %H:%M:%S')}\n\n"
        if lang == "ru"
        else
        f"<b>News affecting currencies</b>\n"
        f"<b>Date:</b> {now.strftime('%d.%m.%Y %H:%M:%S')}\n\n"
    )

    lines = [header]

    for item in rss_items:
        title = item.title
        date = item.get("published", "")[:10]
        impact = explain_impact(title, lang)
        lines.append(f"• <b>{title}</b> ({date})\n{impact}\n")

    NEWS_CACHE[lang] = {"time": now_ts, "data": "\n".join(lines)}


# -----------------------------
# MAIN COMMAND
# -----------------------------
async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ru")

    message = update.message or update.callback_query.message

    now_ts = datetime.datetime.now().timestamp()
    cache = NEWS_CACHE[lang]

    # Если кэш свежий → мгновенный ответ
    if cache["time"] and now_ts - cache["time"] < CACHE_LIFETIME:
        print("[CACHE] Отдаю новости из кэша")
        await message.reply_text(cache["data"], parse_mode="HTML")

        # Обновляем кэш в фоне
        asyncio.create_task(update_cache_in_background(lang))
        return

    # Если кэша нет → показываем "Загружаю..." и обновляем
    await message.reply_text(
        "Загружаю новости..." if lang == "ru" else "Loading news...",
        parse_mode="HTML"
    )

    await update_cache_in_background(lang)

    await message.reply_text(NEWS_CACHE[lang]["data"], parse_mode="HTML")
