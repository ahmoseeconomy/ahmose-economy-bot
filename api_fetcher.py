"""
جلب البيانات اللحظية من الإنترنت
==================================
- أسعار الصرف (مجاني بدون مفتاح)
- سعر الذهب بالأوقية (مجاني)
- معدل التضخم من البنك الدولي (مجاني)
"""

import aiohttp
import logging
import time
from config import (
    EXCHANGE_RATE_API, GOLD_API_URL, WORLD_BANK_INFLATION_API,
    DEFAULT_GOLD_ANNUAL_GROWTH, DEFAULT_CURRENCY_ANNUAL_CHANGE
)

logger = logging.getLogger(__name__)

# ===== كاش بسيط (عشان ما نضغطش على الـ APIs) =====
_cache = {}
CACHE_TTL = 600  # 10 دقائق


def _get_cache(key):
    if key in _cache:
        val, ts = _cache[key]
        if time.time() - ts < CACHE_TTL:
            return val
    return None


def _set_cache(key, val):
    _cache[key] = (val, time.time())


# =============================================
#           أسعار الصرف
# =============================================

async def get_exchange_rates(base: str = "USD") -> dict | None:
    """
    جلب أسعار الصرف مقابل عملة معينة
    المصدر: open.er-api.com (مجاني بدون مفتاح)
    """
    cache_key = f"rates_{base}"
    cached = _get_cache(cache_key)
    if cached:
        return cached

    url = EXCHANGE_RATE_API.format(base=base)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("result") == "success":
                        rates = data.get("rates", {})
                        _set_cache(cache_key, rates)
                        return rates
    except Exception as e:
        logger.error(f"Exchange rate API error: {e}")
    return None


async def get_usd_to_local(currency: str) -> float | None:
    """سعر صرف الدولار مقابل العملة المحلية"""
    rates = await get_exchange_rates("USD")
    if rates and currency in rates:
        return rates[currency]
    return None


# =============================================
#           سعر الذهب
# =============================================

async def get_gold_price_usd() -> float | None:
    """
    جلب سعر جرام الذهب بالدولار
    يجرب أكثر من مصدر (fallback)
    """
    cached = _get_cache("gold_usd")
    if cached:
        return cached

    # المصدر 1: goldprice.org
    try:
        async with aiohttp.ClientSession() as session:
            headers = {"User-Agent": "Mozilla/5.0"}
            async with session.get(
                GOLD_API_URL, headers=headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    items = data.get("items", [])
                    if items:
                        oz_price = items[0].get("xauPrice")
                        if oz_price:
                            gram_price = oz_price / 31.1035
                            _set_cache("gold_usd", gram_price)
                            return gram_price
    except Exception as e:
        logger.error(f"Gold API 1 error: {e}")

    # المصدر 2: frankfurter.app (XAU via exchange rates)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.frankfurter.app/latest?from=XAU&to=USD",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    usd_per_oz = data.get("rates", {}).get("USD")
                    if usd_per_oz:
                        gram_price = usd_per_oz / 31.1035
                        _set_cache("gold_usd", gram_price)
                        return gram_price
    except Exception as e:
        logger.error(f"Gold API 2 error: {e}")

    # المصدر 3: حساب من سعر الصرف (XAU في open.er-api)
    try:
        rates = await get_exchange_rates("USD")
        if rates and "XAU" in rates:
            xau_rate = rates["XAU"]
            if xau_rate > 0:
                oz_price = 1.0 / xau_rate
                gram_price = oz_price / 31.1035
                _set_cache("gold_usd", gram_price)
                return gram_price
    except Exception as e:
        logger.error(f"Gold API 3 error: {e}")

    return None


async def get_gold_price_local(currency: str) -> dict | None:
    """
    سعر جرام الذهب بالعملة المحلية + التوقعات
    يرجع dict فيه: current, forecast_6m, forecast_1y, forecast_3y
    """
    gold_usd = await get_gold_price_usd()
    usd_rate = await get_usd_to_local(currency)

    if gold_usd is None or usd_rate is None:
        return None

    current = gold_usd * usd_rate
    annual_growth = DEFAULT_GOLD_ANNUAL_GROWTH / 100

    return {
        "current_gram_usd": round(gold_usd, 2),
        "current_gram_local": round(current, 2),
        "forecast_6m": round(current * (1 + annual_growth * 0.5), 2),
        "forecast_1y": round(current * (1 + annual_growth), 2),
        "forecast_3y": round(current * (1 + annual_growth) ** 3, 2),
        "growth_rate": DEFAULT_GOLD_ANNUAL_GROWTH,
    }


# =============================================
#           سعر الدولار (بالعملة المحلية)
# =============================================

async def get_hard_currency_data(currency: str) -> dict | None:
    """
    سعر الدولار بالعملة المحلية + التوقعات
    """
    usd_rate = await get_usd_to_local(currency)
    if usd_rate is None:
        return None

    annual_change = DEFAULT_CURRENCY_ANNUAL_CHANGE / 100

    return {
        "current_rate": round(usd_rate, 4),
        "forecast_6m": round(usd_rate * (1 + annual_change * 0.5), 4),
        "forecast_1y": round(usd_rate * (1 + annual_change), 4),
        "forecast_3y": round(usd_rate * (1 + annual_change) ** 3, 4),
        "change_rate": DEFAULT_CURRENCY_ANNUAL_CHANGE,
    }


# =============================================
#           معدل التضخم
# =============================================

async def get_inflation_rate(country_code: str) -> dict | None:
    """
    جلب آخر معدل تضخم منشور من البنك الدولي
    المصدر: World Bank API (مجاني)
    """
    cache_key = f"inflation_{country_code}"
    cached = _get_cache(cache_key)
    if cached:
        return cached

    url = WORLD_BANK_INFLATION_API.format(code=country_code)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if len(data) > 1 and data[1]:
                        for entry in data[1]:
                            val = entry.get("value")
                            year = entry.get("date")
                            if val is not None:
                                result = {
                                    "rate": round(val, 1),
                                    "year": year,
                                    "source": "World Bank"
                                }
                                _set_cache(cache_key, result)
                                return result
    except Exception as e:
        logger.error(f"Inflation API error: {e}")
    return None


# =============================================
#           جلب كل البيانات مرة واحدة
# =============================================

async def fetch_all_data(country_code: str, currency: str) -> dict:
    """
    جلب كل البيانات اللحظية لدولة معينة
    يُستدعى عند كل استخدام للبوت
    """
    gold = await get_gold_price_local(currency)
    hard_currency = await get_hard_currency_data(currency)
    inflation = await get_inflation_rate(country_code)

    return {
        "gold": gold,
        "hard_currency": hard_currency,
        "inflation": inflation,
        "currency": currency,
        "country_code": country_code,
        "fetched": gold is not None or hard_currency is not None,
    }
