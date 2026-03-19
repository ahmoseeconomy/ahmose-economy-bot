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

_cache = {}
CACHE_TTL = 600


def _get_cache(key):
    if key in _cache:
        val, ts = _cache[key]
        if time.time() - ts < CACHE_TTL:
            return val
    return None


def _set_cache(key, val):
    _cache[key] = (val, time.time())


async def get_exchange_rates(base="USD"):
    cache_key = f"rates_{base}"
    cached = _get_cache(cache_key)
    if cached: return cached
    url = EXCHANGE_RATE_API.format(base=base)
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=aiohttp.ClientTimeout(total=10)) as r:
                if r.status == 200:
                    d = await r.json()
                    if d.get("result") == "success":
                        rates = d.get("rates", {})
                        _set_cache(cache_key, rates)
                        return rates
    except Exception as e: logger.error(f"Exchange rate API error: {e}")
    return None

async def get_usd_to_local(currency):
    rates = await get_exchange_rates("USD")
    if rates and currency in rates: return rates[currency]
    return None

async def get_gold_price_usd():
    cached = _get_cache("gold_usd")
    if cached: return cached
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(GOLD_API_URL, headers={"User-Agent":"Mozilla/5.0"}, timeout=aiohttp.ClientTimeout(total=10)) as r:
                if r.status == 200:
                    d = await r.json()
                    items = d.get("items", [])
                    if items:
                        oz = items[0].get("xauPrice")
                        if oz:
                            g = oz / 31.1035
                            _set_cache("gold_usd", g)
                            return g
    except Exception as e: logger.error(f"Gold API error: {e}")
    return None

async def get_gold_price_local(currency):
    gu = await get_gold_price_usd()
    ur = await get_usd_to_local(currency)
    if gu is None or ur is None: return None
    c = gu * ur
    ag = DEFAULT_GOLD_ANNUAL_GROWTH / 100
    return {"current_gram_usd":round(gu,2),"current_gram_local":round(c,2),"forecast_6m":round(c*(1+ag*0.5),2),"forecast_1y":round(c*(1+ag),2),"forecast_3y":round(c*(1+ag)**3,2),"growth_rate":DEFAULT_GOLD_ANNUAL_GROWTH}

async def get_hard_currency_data(currency):
    ur = await get_usd_to_local(currency)
    if ur is None: return None
    ac = DEFAULT_CURRENCY_ANNUAL_CHANGE / 100
    return {"current_rate":round(ur,4),"forecast_6m":round(ur*(1+ac*0.5),4),"forecast_1y":round(ur*(1+ac),4),"forecast_3y":round(ur*(1+ac)**3,4),"change_rate":DEFAULT_CURRENCY_ANNUAL_CHANGE}

async def get_inflation_rate(country_code):
    ck = f"inflation_{country_code}"
    cached = _get_cache(ck)J    if cached: return cached
    url = WORLD_BANK_INFLATION_API.format(code=country_code)
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=aiohttp.ClientTimeout(total=10)) as r:
                if r.status == 200:
                    d = await r.json()
                    if len(d) > 1 and d[1]:
                        for e in d[1]:
                            v = e.get("value")
                            y = e.get("date")
                            if v is not None:
                                res = {"rate":round(v,1),"year":y,"source":"World Bank"}
                                _set_cache(ck, res)
                                return res
    except Exception as e: logger.error(f"Inflation API error: {e}")
    return None

async def fetch_all_data(country_code, currency):
    gold = await get_gold_price_local(currency)
    hc = await get_hard_currency_data(currency)
    inf = await get_inflation_rate(country_code)
    return {"gold":gold,"hard_currency":hc,"inflation":inf,"currency":currency,"country_code":country_code,"fetched":gold is not None or hc is not None}
