# handlers/converter.py
import re
import aiohttp
import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from i18n import t

CRYPTO = {"BTC", "ETH", "BNB", "SOL", "XAU"}
FIAT = {"USD", "EUR", "RUB", "GBP", "UAH", "KZT", "BYN", "JPY", "TRY", "CNY"}
ALL = CRYPTO.union(FIAT)

NUMBER_RE = re.compile(r"[-+]?\d[\d\s,\.]*\d|\d")
CURRENCY_RE = re.compile(r"\b(BTC|ETH|BNB|SOL|XAU|[A-Z]{3})\b", re.IGNORECASE)

REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=6)

COINGECKO_MAP = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "BNB": "binancecoin",
    "SOL": "solana",
    "XAU": "gold"
}

def _norm_number(s: str):
    s = s.replace(" ", "").replace(",", ".")
    try:
        return float(s)
    except Exception:
        return None

def _fmt_value(v: float):
    if v is None:
        return "—"
    if v >= 1:
        return f"{v:,.4f}"
    if v >= 0.0001:
        return f"{v:,.6f}"
    return f"{v:.8f}"


async def converter_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ru")
    message = update.message or (update.callback_query and update.callback_query.message)
    if not message:
        return

    context.user_data["converter_mode"] = True
    context.user_data["converter_mode_ts"] = asyncio.get_event_loop().time()

    try:
        context.user_data["converter_ignore_mid"] = message.message_id
    except Exception:
        context.user_data.pop("converter_ignore_mid", None)

    await message.reply_text(t(context, "converter.enabled"))


async def convert_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("converter_mode"):
        return

    ignore_mid = context.user_data.get("converter_ignore_mid")
    try:
        incoming_mid = update.message.message_id if update.message else None
    except Exception:
        incoming_mid = None

    if ignore_mid is not None and incoming_mid == ignore_mid:
        context.user_data.pop("converter_ignore_mid", None)
        return

    ts = context.user_data.get("converter_mode_ts")
    if ts:
        try:
            now = asyncio.get_event_loop().time()
            if now - ts > 300:
                context.user_data.pop("converter_mode", None)
                context.user_data.pop("converter_mode_ts", None)
                context.user_data.pop("converter_ignore_mid", None)
                return
        except Exception:
            pass

    text_raw = (update.message.text or "").strip()
    if not text_raw:
        return

    numbers_quick = NUMBER_RE.findall(text_raw.upper())
    currencies_quick = CURRENCY_RE.findall(text_raw.upper())
    if not numbers_quick or len(currencies_quick) < 2:
        await update.message.reply_text(t(context, "converter.no_amount"))
        return

    text = text_raw.upper()
    numbers = NUMBER_RE.findall(text)
    currencies = CURRENCY_RE.findall(text)
    amounts = [_norm_number(n) for n in numbers]
    amounts = [a for a in amounts if a is not None]
    currencies = [c.upper() for c in currencies]

    lang = context.user_data.get("lang", "ru")

    if not amounts:
        await update.message.reply_text(t(context, "converter.no_amount"))
        return
    if len(currencies) < 2:
        await update.message.reply_text(t(context, "converter.need_two"))
        return

    amount = amounts[0]
    from_currency = currencies[0]
    to_currency = currencies[1]

    if from_currency not in ALL or to_currency not in ALL:
        await update.message.reply_text(
            t(context, "converter.unknown_currency", codes=", ".join(sorted(ALL)))
        )
        return

    result = None
    rate = None
    source = None

    async with aiohttp.ClientSession(timeout=REQUEST_TIMEOUT) as session:
        try:
            # FIAT → FIAT через Open ER API
            if from_currency in FIAT and to_currency in FIAT:
                url = f"https://open.er-api.com/v6/latest/{from_currency}"
                async with session.get(url) as resp:
                    data = await resp.json()
                    rates = data.get("rates", {})
                    if to_currency in rates:
                        rate = float(rates[to_currency])
                        result = amount * rate
                        source = "open.er-api.com"

            # CRYPTO → FIAT
            elif from_currency in CRYPTO:
                cg_id = COINGECKO_MAP.get(from_currency)
                vs = to_currency.lower()
                url = f"https://api.coingecko.com/api/v3/simple/price?ids={cg_id}&vs_currencies={vs}"
                async with session.get(url) as resp:
                    data = await resp.json()
                    val = data.get(cg_id, {}).get(vs)
                    if val is not None:
                        rate = float(val)
                        result = amount * rate
                        source = "CoinGecko"

            # FIAT → CRYPTO
            elif to_currency in CRYPTO:
                cg_id = COINGECKO_MAP.get(to_currency)
                vs = from_currency.lower()
                url = f"https://api.coingecko.com/api/v3/simple/price?ids={cg_id}&vs_currencies={vs}"
                async with session.get(url) as resp:
                    data = await resp.json()
                    price = data.get(cg_id, {}).get(vs)
                    if price is not None:
                        price = float(price)
                        rate = price
                        result = amount / price if price != 0 else None
                        source = "CoinGecko"

            # Резервный источник
            if result is None:
                url = f"https://min-api.cryptocompare.com/data/price?fsym={from_currency}&tsyms={to_currency}"
                async with session.get(url) as resp:
                    data = await resp.json()
                    val = data.get(to_currency)
                    if val is not None:
                        rate = float(val)
                        result = amount * rate
                        source = "CryptoCompare"

        except asyncio.TimeoutError:
            await update.message.reply_text(t(context, "converter.timeout"))
            return
        except Exception:
            await update.message.reply_text(t(context, "converter.error"))
            return

    if result is None:
        await update.message.reply_text(t(context, "converter.error"))
        return

    context.user_data.pop("converter_mode", None)
    context.user_data.pop("converter_mode_ts", None)
    context.user_data.pop("converter_ignore_mid", None)

    if rate is not None:
        await update.message.reply_text(
            f"💸 1 {from_currency} = {_fmt_value(rate)} {to_currency}\nSource: {source}"
        )

    await update.message.reply_text(
        f"💸 {amount} {from_currency} = {_fmt_value(result)} {to_currency}"
    )
