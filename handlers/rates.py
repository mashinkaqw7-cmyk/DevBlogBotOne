# handlers/rates.py
import datetime
import pytz
import aiohttp
from telegram import Update
from telegram.ext import ContextTypes
from i18n import t

# Попытка импортировать wcwidth для корректного подсчёта визуальной ширины символов (эмодзи и т.д.)
try:
    from wcwidth import wcswidth
except Exception:
    wcswidth = None  # fallback — будем использовать len()


async def fetch_rates():
    """Получает курсы валют за 1 USD через exchangerate.host"""
    url = "https://open.er-api.com/v6/latest/USD"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                data = await resp.json()
                return data.get("rates", {})
    except Exception:
        return {}  # если API упал — вернём пустой словарь


def _display_width(s: str) -> int:
    if s is None:
        return 0
    if wcswidth:
        try:
            w = wcswidth(s)
            return w if w >= 0 else len(s)
        except Exception:
            return len(s)
    return len(s)


def _pad_right(s: str, width: int) -> str:
    cur = _display_width(s)
    if cur >= width:
        return s
    return s + " " * (width - cur)


def _pad_left(s: str, width: int) -> str:
    cur = _display_width(s)
    if cur >= width:
        return s
    return " " * (width - cur) + s


def _format_rate(value: float) -> str:
    if value is None:
        return "—"
    if value >= 1:
        return f"{value:,.4f}"
    if value >= 0.0001:
        return f"{value:,.6f}"
    return f"{value:.8f}"


def _make_box_line(parts, widths, left, mid, sep, right):
    segs = []
    for w in widths:
        segs.append("─" * (w + 2))
    return left + mid.join(segs) + right


async def rates_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ru")
    message = update.effective_message

    tz = pytz.timezone("Europe/Moscow" if lang == "ru" else "America/New_York")
    now = datetime.datetime.now(tz)

    header_text = t({'user_data': {'lang': lang}}, "rates.header")
    updated_text = t({'user_data': {'lang': lang}}, "rates.updated",
                     time=now.strftime('%d.%m.%Y %H:%M:%S'))

    # Загружаем курсы
    rates_api = await fetch_rates()

    # Если API не ответил — покажем заглушку
    if not rates_api:
        await message.reply_text("❌ Ошибка получения курсов. Попробуйте позже.")
        return

    # Формируем список валют
    currencies = [
        ("EUR", rates_api.get("EUR"), "€"),
        ("RUB", rates_api.get("RUB"), "₽"),
        ("GBP", rates_api.get("GBP"), "£"),
        ("UAH", rates_api.get("UAH"), "₴"),
        ("KZT", rates_api.get("KZT"), "₸"),
        ("BYN", rates_api.get("BYN"), "Br"),
        ("JPY", rates_api.get("JPY"), "¥"),
        ("TRY", rates_api.get("TRY"), "₺"),
        ("CNY", rates_api.get("CNY"), "¥"),

        # Крипта — пока оставляем статичной (можно подключить CoinGecko)
        ("BTC", 0.000014, "₿"),
        ("ETH", 0.00021, "Ξ"),
        ("BNB", 0.0015, "B"),
        ("SOL", 0.022, "S"),
        ("XAU", 0.00052, "Au"),
    ]

    # Подготовка форматированных строк
    codes = [c for c, _, _ in currencies]
    rates = [_format_rate(r) for _, r, _ in currencies]
    syms = [s for _, _, s in currencies]

    col_code = "Валюта" if lang == "ru" else "Currency"
    col_rate = "Курс" if lang == "ru" else "Rate"
    col_sym = "Символ" if lang == "ru" else "Symbol"

    w_code = max(_display_width(col_code), max(_display_width(x) for x in codes))
    w_rate = max(_display_width(col_rate), max(_display_width(x) for x in rates))
    w_sym = max(_display_width(col_sym), max(_display_width(x) for x in syms))

    widths = [w_code, w_rate, w_sym]

    top = _make_box_line(None, widths, "┌", "┬", "─", "┐")
    mid = _make_box_line(None, widths, "├", "┼", "─", "┤")
    bottom = _make_box_line(None, widths, "└", "┴", "─", "┘")

    lines = []
    lines.append(top)

    col_code_p = _pad_right(col_code, w_code)
    col_rate_p = _pad_left(col_rate, w_rate)
    col_sym_p = _pad_right(col_sym, w_sym)
    lines.append(f"│ {col_code_p} │ {col_rate_p} │ {col_sym_p} │")
    lines.append(mid)

    for code, rate_str, sym in zip(codes, rates, syms):
        code_p = _pad_right(code, w_code)
        rate_p = _pad_left(rate_str, w_rate)
        sym_p = _pad_right(sym, w_sym)
        lines.append(f"│ {code_p} │ {rate_p} │ {sym_p} │")

    lines.append(bottom)

    table = "\n".join(lines)

    text = f"<pre>{header_text}\n{updated_text}\n\n{table}</pre>"

    try:
        await message.reply_text(text, parse_mode="HTML")
    except Exception:
        chat_id = update.effective_chat.id if update.effective_chat else None
        if chat_id:
            await context.bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")
