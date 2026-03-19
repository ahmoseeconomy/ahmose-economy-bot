"""
Ø¨ÙØª Ø§ÙØªØµØ§Ø¯ Ø£Ø­ÙØ³ v2 - Ø­Ø§Ø³Ø¨Ø© Ø§ÙØªØ¶Ø®Ù ÙØ§ÙØ§Ø³ØªØ«ÙØ§Ø±
=================================================
Ø¨ÙØ§ÙØ§Øª ÙØ­Ø¸ÙØ© | ÙÙ Ø¯ÙÙ Ø§ÙØ¹Ø§ÙÙ | Ø£ÙÙØ§Ù ÙØ³ØªÙØ­Ø§Ø© ÙÙ Ø§ÙÙÙØ¬Ù
"""

import asyncio
import logging
import os
import sys
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardButton,
    InlineKeyboardMarkup, FSInputFile
)
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ChatMemberStatus, ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from config import (
    BOT_TOKEN, CHANNEL_USERNAME, CHANNEL_LINK, ADMIN_IDS,
    WEBHOOK_PATH, WEBHOOK_URL, WEBAPP_HOST, WEBAPP_PORT,
    USE_WEBHOOK, LOGO_PATH
)
from database import (
    init_db, save_user, get_user_country, get_all_user_ids,
    get_users_count, get_users_by_country, get_setting, set_setting,
    get_all_settings, block_user
)
from countries import ALL_COUNTRIES, search_countries, get_country_by_code, get_countries_page
from api_fetcher import fetch_all_data, get_gold_price_local, get_hard_currency_data

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
router = Router()


# ââââââââââââââââââââââââââââââââââââââ
#              Ø­Ø§ÙØ§Øª FSM
# ââââââââââââââââââââââââââââââââââââââ

class InvestForm(StatesGroup):
    waiting_country = State()
    waiting_amount = State()
    waiting_duration = State()
    waiting_tool = State()
    waiting_bank_rate = State()  # Ø§ÙÙØ³ØªØ®Ø¯Ù ÙØ¯Ø®Ù ÙØ³Ø¨Ø© Ø§ÙØ´ÙØ§Ø¯Ø©


class AdminStates(StatesGroup):
    waiting_setting_value = State()
    waiting_broadcast_message = State()
    waiting_link_text = State()
    waiting_link_url = State()


# ââââââââââââââââââââââââââââââââââââââ
#              Ø£Ø¯ÙØ§Øª ÙØ³Ø§Ø¹Ø¯Ø©
# ââââââââââââââââââââââââââââââââââââââ

# ââ Ø£ÙÙØ§Ù ÙØ³ØªÙØ­Ø§Ø© ÙÙ Ø§ÙÙÙØ¬Ù (ÙÙØ§Ø³ØªØ®Ø¯Ø§Ù ÙÙ Ø§ÙØ±Ø³Ø§Ø¦Ù) ââ
# Ø°ÙØ¨Ù âï¸ | Ø£Ø³ÙØ¯ ð¤ | Ø£Ø²Ø±Ù Ø³ÙØ§Ù ð· | Ø±ÙØ§Ø¯Ù âï¸
# ÙØ³ØªØ®Ø¯Ù Ø¥ÙÙÙØ¬Ù Ø°ÙØ¨ÙØ© + Ø®Ø·ÙØ· ÙØ±Ø¹ÙÙÙØ©

PHARAOH_LINE = "âââââââââââââââââââ"
GOLD_DIAMOND = "â"
ANKH = "â¥"

def fmt(n: float) -> str:
    if n == int(n):
        return f"{int(n):,}"
    return f"{n:,.2f}"


async def check_subscription(user_id: int) -> bool:
    # TODO: re-enable after testing
    return True


def sub_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ð¢ Ø§Ø´ØªØ±Ù ÙÙ Ø§ÙÙÙØ§Ø©", url=CHANNEL_LINK)],
        [InlineKeyboardButton(text=f"{ANKH} ØªØ­ÙÙØª ÙÙ Ø§ÙØ§Ø´ØªØ±Ø§Ù", callback_data="check_sub")]
    ])


async def send_logo(chat_id: int, caption: str, reply_markup=None):
    """Ø¥Ø±Ø³Ø§Ù Ø§ÙÙÙØ¬Ù ÙØ¹ Ø±Ø³Ø§ÙØ©"""
    if os.path.exists(LOGO_PATH):
        photo = FSInputFile(LOGO_PATH)
        await bot.send_photo(
            chat_id=chat_id,
            photo=photo,
            caption=caption,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    else:
        await bot.send_message(
            chat_id=chat_id,
            text=caption,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )


async def result_buttons() -> InlineKeyboardMarkup:
    link_text = await get_setting("result_link_text")
    link_url = await get_setting("result_link_url")
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"ð {link_text}", url=link_url)],
        [InlineKeyboardButton(text=f"{ANKH} Ø­Ø³Ø§Ø¨ Ø¬Ø¯ÙØ¯", callback_data="new_calc")]
    ])


def is_admin(uid: int) -> bool:
    return uid in ADMIN_IDS


def country_keyboard(page: int = 0) -> InlineKeyboardMarkup:
    """Ø£Ø²Ø±Ø§Ø± Ø§Ø®ØªÙØ§Ø± Ø§ÙØ¯ÙÙØ© ÙØ¹ Ø³ÙØ±ÙÙ"""
    countries, has_prev, has_next = get_countries_page(page, per_page=8)

    rows = []
    for i in range(0, len(countries), 2):
        row = [InlineKeyboardButton(
            text=f"{countries[i]['flag']} {countries[i]['name_ar']}",
            callback_data=f"country_{countries[i]['code']}"
        )]
        if i + 1 < len(countries):
            row.append(InlineKeyboardButton(
                text=f"{countries[i+1]['flag']} {countries[i+1]['name_ar']}",
                callback_data=f"country_{countries[i+1]['code']}"
            ))
        rows.append(row)

    # Ø£Ø²Ø±Ø§Ø± Ø§ÙØªÙÙÙ
    nav = []
    if has_prev:
        nav.append(InlineKeyboardButton(text="âï¸ Ø§ÙØ³Ø§Ø¨Ù", callback_data=f"cpage_{page-1}"))
    nav.append(InlineKeyboardButton(text=f"ð {page+1}", callback_data="noop"))
    if has_next:
        nav.append(InlineKeyboardButton(text="Ø§ÙØªØ§ÙÙ â¶ï¸", callback_data=f"cpage_{page+1}"))
    rows.append(nav)

    return InlineKeyboardMarkup(inline_keyboard=rows)


def search_results_keyboard(results: list) -> InlineKeyboardMarkup:
    """Ø£Ø²Ø±Ø§Ø± ÙØªØ§Ø¦Ø¬ Ø§ÙØ¨Ø­Ø«"""
    rows = []
    for c in results:
        rows.append([InlineKeyboardButton(
            text=f"{c['flag']} {c['name_ar']} ({c['currency']})",
            callback_data=f"country_{c['code']}"
        )])
    rows.append([InlineKeyboardButton(text="ð Ø¹Ø±Ø¶ ÙÙ Ø§ÙØ¯ÙÙ", callback_data="cpage_0")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def duration_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="6ï¸â£ Ø´ÙÙØ±", callback_data="dur_6m"),
        InlineKeyboardButton(text="1ï¸â£ Ø³ÙØ©", callback_data="dur_1y"),
        InlineKeyboardButton(text="3ï¸â£ Ø³ÙÙØ§Øª", callback_data="dur_3y"),
    ]])


def tool_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ð¦ Ø´ÙØ§Ø¯Ø§Øª Ø¨ÙÙÙØ©", callback_data="tool_bank")],
        [InlineKeyboardButton(text=f"ð¥ Ø°ÙØ¨ (Ø³Ø¹Ø± ÙØ­Ø¸Ù)", callback_data="tool_gold")],
        [InlineKeyboardButton(text="ðµ Ø¹ÙÙØ© ØµØ¹Ø¨Ø© (Ø¯ÙÙØ§Ø±)", callback_data="tool_usd")],
    ])


# ââââââââââââââââââââââââââââââââââââââ
#           Ø£ÙØ§ÙØ± Ø§ÙÙØ³ØªØ®Ø¯Ù
# ââââââââââââââââââââââââââââââââââââââ

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await save_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )

    is_sub = await check_subscription(message.from_user.id)
    if not is_sub:
        await send_logo(
            message.chat.id,
            f"<b>{GOLD_DIAMOND} Ø­Ø§Ø³Ø¨ Ø¹ÙÙ ÙÙÙØ³Ù {GOLD_DIAMOND}</b>\n"
            f"{PHARAOH_LINE}\n\n"
            "Ø§ÙØªØ¶Ø®Ù ÙØ´ Ø¨ÙØ³ØªÙÙ Ø­Ø¯\n"
            "Ø§Ø¹Ø±Ù Ø¯ÙÙÙØªÙ: Ø§Ø³ØªØ«ÙØ§Ø±Ù Ø¨ÙÙØ³Ø¨\n"
            "ÙÙØ§ Ø¨ÙØ®Ø³Ø± ÙÙ ØºÙØ± ÙØ§ ØªØ­Ø³Ø â¡\n\n"
            "â ï¸ ÙØ§Ø²Ù ØªÙÙÙ ÙØ´ØªØ±Ù ÙÙ Ø§ÙÙÙØ§Ø© Ø§ÙØ£ÙÙ\n\n"
            "ð¢ Ø§Ø´ØªØ±Ù ÙØ¨Ø¹Ø¯ÙÙ Ø§Ø¶ØºØ· ØªØ­ÙÙ ð",
            reply_markup=sub_kb()
        )
        return

    await ask_country(message.chat.id, state)


async def ask_country(chat_id: int, state: FSMContext):
    """Ø³Ø¤Ø§Ù Ø§ÙÙØ³ØªØ®Ø¯Ù Ø¹Ù Ø¨ÙØ¯Ù"""
    await state.set_state(InvestForm.waiting_country)
    await send_logo(
        chat_id,
        f"<b>{GOLD_DIAMOND} Ø­Ø§Ø³Ø¨Ø© Ø§ÙØªØ¶Ø®Ù ÙØ§ÙØ§Ø³ØªØ«ÙØ§Ø± {GOLD_DIAMOND}</b>\n"
        f"{PHARAOH_LINE}\n\n"
        "ð <b>Ø§Ø®ØªØ§Ø± Ø¨ÙØ¯Ù</b> Ø¹Ø´Ø§Ù ÙØ¬ÙØ¨ÙÙ Ø§ÙØ£Ø³Ø¹Ø§Ø± Ø§ÙÙØ­Ø¸ÙØ©\n\n"
        "âï¸ <b>Ø§ÙØªØ¨ Ø§Ø³Ù Ø¨ÙØ¯Ù</b> (Ø¹Ø±Ø¨Ù Ø£Ù Ø¥ÙØ¬ÙÙØ²Ù)\n"
        "Ø£Ù Ø§Ø®ØªØ§Ø± ÙÙ Ø§ÙÙØ§Ø¦ÙØ© ð",
        reply_markup=country_keyboard(0)
    )


@router.callback_query(F.data == "check_sub")
async def check_sub_cb(callback: CallbackQuery, state: FSMContext):
    is_sub = await check_subscription(callback.from_user.id)
    if is_sub:
        await callback.message.delete()
        await ask_country(callback.message.chat.id, state)
    else:
        await callback.answer("â ÙØ³Ù ÙØ´ØªØ±Ù! Ø§Ø´ØªØ±Ù Ø§ÙØ£ÙÙ", show_alert=True)


@router.callback_query(F.data == "new_calc")
async def new_calc_cb(callback: CallbackQuery, state: FSMContext):
    is_sub = await check_subscription(callback.from_user.id)
    if not is_sub:
        await callback.message.answer("â ï¸ Ø§Ø´ØªØ±Ù ÙÙ Ø§ÙÙÙØ§Ø© Ø§ÙØ£ÙÙ!", reply_markup=sub_kb())
        return
    await ask_country(callback.message.chat.id, state)


# ââ ØªØµÙØ­ Ø§ÙØ¯ÙÙ ââ

@router.callback_query(F.data == "noop")
async def noop_cb(callback: CallbackQuery):
    await callback.answer()


@router.callback_query(F.data.startswith("cpage_"))
async def country_page(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data.split("_")[1])
    try:
        await callback.message.edit_reply_markup(reply_markup=country_keyboard(page))
    except Exception:
        pass


# ââ Ø§ÙØ¨Ø­Ø« Ø¹Ù Ø§ÙØ¯ÙÙØ© Ø¨Ø§ÙÙØªØ§Ø¨Ø© ââ
@router.message(InvestForm.waiting_country)
async def search_country_text(message: Message, state: FSMContext):
    """Ø§ÙÙØ³ØªØ®Ø¯Ù ÙØªØ¨ Ø§Ø³Ù Ø¨ÙØ¯Ù Ø¨Ø¯Ù ÙØ§ ÙØ¶ØºØ· Ø²Ø±"""
    query = message.text.strip()
    results = search_countries(query, limit=6)

    if not results:
        await message.answer(
            f"â ÙÙÙØ´ Ø¯ÙÙØ© Ø§Ø³ÙÙØ§ <b>{query}</b>\n\n"
            "Ø¬Ø±Ø¨ ØªÙØªØ¨ Ø§Ø³Ù ØªØ§ÙÙ Ø£Ù Ø§Ø®ØªØ§Ø± ÙÙ Ø§ÙÙØ§Ø¦ÙØ© ð",
            parse_mode=ParseMode.HTML,
            reply_markup=country_keyboard(0)
        )
        return

    if len(results) == 1:
        # ÙØªÙØ¬Ø© ÙØ§Ø­Ø¯Ø© â Ø§Ø®ØªØ§Ø±ÙØ§ ÙØ¨Ø§Ø´Ø±Ø©
        country = results[0]
        await _select_country(message.chat.id, message.from_user, country, state)
        return

    # Ø£ÙØ«Ø± ÙÙ ÙØªÙØ¬Ø© â Ø¹Ø±Ø¶ÙØ§ ÙØ£Ø²Ø±Ø§Ø±
    await message.answer(
        f"ð ÙØªØ§Ø¦Ø¬ Ø§ÙØ¨Ø­Ø« Ø¹Ù <b>{query}</b>:",
        parse_mode=ParseMode.HTML,
        reply_markup=search_results_keyboard(results)
    )


# ââ Ø§Ø®ØªÙØ§Ø± Ø§ÙØ¯ÙÙØ© ââ

@router.callback_query(F.data.startswith("country_"), InvestForm.waiting_country)
async def select_country_cb(callback: CallbackQuery, state: FSMContext):
    code = callback.data.replace("country_", "")
    country = get_country_by_code(code)
    if not country:
        await callback.answer("â Ø®Ø·Ø£", show_alert=True)
        return
    try:
        await callback.message.delete()
    except Exception:
        pass
    await _select_country(callback.message.chat.id, callback.from_user, country, state)


async def _select_country(chat_id: int, user, country: dict, state: FSMContext):
    """ÙØ¹Ø§ÙØ¬Ø© Ø§Ø®ØªÙØ§Ø± Ø§ÙØ¯ÙÙØ© (ÙØ´ØªØ±ÙØ© Ø¨ÙÙ Ø§ÙØ¶ØºØ· ÙØ§ÙÙØªØ§Ø¨Ø©)"""
    await save_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        country_code=country["code"],
        currency=country["currency"]
    )

    loading = await bot.send_message(
        chat_id,
        f"â³ Ø¬Ø§Ø±Ù Ø¬ÙØ¨ Ø§ÙØ¨ÙØ§ÙØ§Øª Ø§ÙÙØ­Ø¸ÙØ© ÙÙ {country['flag']} {country['name_ar']}..."
    )

    live_data = await fetch_all_data(country["code"], country["currency"])
    await state.update_data(country=country, live_data=live_data)

    summary = f"<b>{GOLD_DIAMOND} {country['flag']} Ø£Ø³Ø¹Ø§Ø± {country['name_ar']} Ø§ÙÙØ­Ø¸ÙØ© {GOLD_DIAMOND}</b>\n"
    summary += f"{PHARAOH_LINE}\n\n"

    if live_data["gold"]:
        g = live_data["gold"]
        summary += f"ð¥ <b>Ø§ÙØ°ÙØ¨:</b> {fmt(g['current_gram_local'])} {country['currency_name']}/Ø¬Ø±Ø§Ù\n"
        summary += f"   <i>(${fmt(g['current_gram_usd'])} Ø¹Ø§ÙÙÙØ§Ù)</i>\n\n"

    if live_data["hard_currency"]:
        h = live_data["hard_currency"]
        summary += f"ðµ <b>Ø§ÙØ¯ÙÙØ§Ø±:</b> {fmt(h['current_rate'])} {country['currency_name']}\n\n"

    if live_data["inflation"]:
        inf_data = live_data["inflation"]
        summary += f"ð <b>Ø§ÙØªØ¶Ø®Ù:</b> {inf_data['rate']}% <i>(Ø¢Ø®Ø± Ø¨ÙØ§ÙØ§Øª: {inf_data['year']} - {inf_data['source']})</i>\n\n"
    else:
        fb = await get_setting("fallback_inflation")
        summary += f"ð <b>Ø§ÙØªØ¶Ø®Ù:</b> {fb}% <i>(ØªÙØ¯ÙØ±Ù)</i>\n\n"

    summary += f"{PHARAOH_LINE}\n"
    summary += "ð° <b>Ø§ÙØªØ¨ Ø§ÙÙØ¨ÙØº Ø§ÙÙÙ Ø¹Ø§ÙØ² ØªØ³ØªØ«ÙØ±Ù</b>\n"
    summary += f"<i>(Ø£Ø±ÙØ§Ù ÙÙØ· Ø¨Ù {country['currency_name']})</i>"

    await state.set_state(InvestForm.waiting_amount)
    try:
        await loading.delete()
    except Exception:
        pass
    await bot.send_message(chat_id, summary, parse_mode=ParseMode.HTML)


# ââ Ø¥Ø¯Ø®Ø§Ù Ø§ÙÙØ¨ÙØº ââ

@router.message(InvestForm.waiting_amount)
async def receive_amount(message: Message, state: FSMContext):
    text = message.text.strip().replace(",", "").replace("Ù¬", "").replace("Ø", "")
    try:
        amount = float(text)
        if amount <= 0:
            raise ValueError
        if amount > 999_999_999_999:
            await message.answer("â ï¸ Ø§ÙÙØ¨ÙØº ÙØ¨ÙØ± Ø£ÙÙ!")
            return
    except (ValueError, TypeError):
        await message.answer(
            "â <b>Ø¥Ø¯Ø®Ø§Ù ØºÙØ± ØµØ­ÙØ­</b>\n\nØ§ÙØªØ¨ Ø£Ø±ÙØ§Ù ÙÙØ·\nÙØ«Ø§Ù: <code>100000</code>",
            parse_mode=ParseMode.HTML
        )
        return

    data = await state.get_data()
    country = data["country"]
    await state.update_data(amount=amount)
    await state.set_state(InvestForm.waiting_duration)
    await message.answer(
        f"ð° Ø§ÙÙØ¨ÙØº: <b>{fmt(amount)} {country['currency_name']}</b>\n\n"
        "â³ Ø§Ø®ØªØ§Ø± ÙØ¯Ø© Ø§ÙØ§Ø³ØªØ«ÙØ§Ø± ð",
        reply_markup=duration_kb(),
        parse_mode=ParseMode.HTML
    )


# ââ Ø§Ø®ØªÙØ§Ø± Ø§ÙÙØ¯Ø© ââ

@router.callback_query(F.data.startswith("dur_"), InvestForm.waiting_duration)
async def receive_duration(callback: CallbackQuery, state: FSMContext):
    dur_map = {"dur_6m": ("6 Ø´ÙÙØ±", 0.5), "dur_1y": ("Ø³ÙØ©", 1.0), "dur_3y": ("3 Ø³ÙÙØ§Øª", 3.0)}
    dur_text, dur_years = dur_map[callback.data]

    await state.update_data(duration_text=dur_text, duration_years=dur_years, dur_key=callback.data)
    await state.set_state(InvestForm.waiting_tool)

    data = await state.get_data()
    country = data["country"]
    await callback.message.edit_text(
        f"ð° Ø§ÙÙØ¨ÙØº: <b>{fmt(data['amount'])} {country['currency_name']}</b>\n"
        f"â³ Ø§ÙÙØ¯Ø©: <b>{dur_text}</b>\n\n"
        "ð Ø§Ø®ØªØ§Ø± Ø£Ø¯Ø§Ø© Ø§ÙØ§Ø³ØªØ«ÙØ§Ø± ð",
        reply_markup=tool_kb(),
        parse_mode=ParseMode.HTML
    )


# ââ Ø§Ø®ØªÙØ§Ø± Ø§ÙØ£Ø¯Ø§Ø© ââ

@router.callback_query(F.data.startswith("tool_"), InvestForm.waiting_tool)
async def receive_tool(callback: CallbackQuery, state: FSMContext):
    tool = callback.data

    if tool == "tool_bank":
        # Ø§ÙØ´ÙØ§Ø¯Ø©: Ø§ÙÙØ³ØªØ®Ø¯Ù ÙØ¯Ø®Ù ÙØ³Ø¨Ø© Ø§ÙÙØ§Ø¦Ø¯Ø© Ø¨ÙÙØ³Ù
        await state.update_data(tool=tool)
        await state.set_state(InvestForm.waiting_bank_rate)
        await callback.message.edit_text(
            "ð¦ <b>Ø´ÙØ§Ø¯Ø§Øª Ø¨ÙÙÙØ©</b>\n"
            f"{PHARAOH_LINE}\n\n"
            "ð <b>Ø§ÙØªØ¨ ÙØ³Ø¨Ø© Ø§ÙÙØ§Ø¦Ø¯Ø© Ø§ÙØ³ÙÙÙØ© ÙØ´ÙØ§Ø¯ØªÙ</b>\n"
            "<i>(Ø±ÙÙ ÙÙØ· - ÙØ«Ø§Ù: 27)</i>\n\n"
            "ð¡ Ø§ÙÙØ³Ø¨Ø© Ø¨ØªØ®ØªÙÙ Ø­Ø³Ø¨ Ø§ÙØ¨ÙÙ ÙÙÙØ¹ Ø§ÙØ´ÙØ§Ø¯Ø©",
            parse_mode=ParseMode.HTML
        )
        return

    # Ø§ÙØ°ÙØ¨ ÙØ§ÙØ¯ÙÙØ§Ø±: Ø­Ø³Ø§Ø¨ ÙØ¨Ø§Ø´Ø±
    await state.update_data(tool=tool)
    await calculate_result(callback, state)


# ââ Ø¥Ø¯Ø®Ø§Ù ÙØ³Ø¨Ø© Ø§ÙØ´ÙØ§Ø¯Ø© Ø§ÙØ¨ÙÙÙØ© ââ

@router.message(InvestForm.waiting_bank_rate)
async def receive_bank_rate(message: Message, state: FSMContext):
    try:
        rate = float(message.text.strip().replace("%", ""))
        if rate <= 0 or rate > 100:
            raise ValueError
    except (ValueError, TypeError):
        await message.answer("â Ø§ÙØªØ¨ ÙØ³Ø¨Ø© ØµØ­ÙØ­Ø© (ÙØ«Ø§Ù: 27)")
        return

    await state.update_data(bank_rate=rate)

    # ÙØ­Ø§ÙÙ callback Ø¹Ø´Ø§Ù ÙØ³ØªØ®Ø¯Ù ÙÙØ³ Ø§ÙØ¯Ø§ÙØ©
    data = await state.get_data()
    await calculate_and_send(message.chat.id, data, state)


# ââââââââââââââââââââââââââââââââââââââ
#           Ø­Ø³Ø§Ø¨ Ø§ÙÙØªÙØ¬Ø©
# ââââââââââââââââââââââââââââââââââââââ

async def calculate_result(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await callback.message.edit_text("â³ Ø¬Ø§Ø±Ù Ø§ÙØ­Ø³Ø§Ø¨...")
    await calculate_and_send(callback.message.chat.id, data, state)


async def calculate_and_send(chat_id: int, data: dict, state: FSMContext):
    amount = data["amount"]
    dur_years = data["duration_years"]
    dur_text = data["duration_text"]
    dur_key = data["dur_key"]
    tool = data["tool"]
    country = data["country"]
    live = data["live_data"]
    currency_name = country["currency_name"]

    # ââ Ø§ÙØªØ¶Ø®Ù ââ
    if live["inflation"]:
        inflation_rate = live["inflation"]["rate"]
        inflation_source = f"({live['inflation']['source']} - {live['inflation']['year']})"
    else:
        inflation_rate = await get_setting("fallback_inflation")
        inflation_source = "(ØªÙØ¯ÙØ±Ù)"

    inf = inflation_rate / 100
    purchasing_loss = amount * (1 - (1 / ((1 + inf) ** dur_years)))

    result = ""

    # ââââââââ Ø´ÙØ§Ø¯Ø§Øª Ø¨ÙÙÙØ© ââââââââ
    if tool == "tool_bank":
        rate = data["bank_rate"] / 100
        total_return = amount * rate * dur_years
        final = amount + total_return
        real_profit = total_return - purchasing_loss

        result = (
            f"<b>ð¦ ÙØªÙØ¬Ø© Ø§ÙØ§Ø³ØªØ«ÙØ§Ø± ÙÙ Ø´ÙØ§Ø¯Ø§Øª Ø¨ÙÙÙØ©</b>\n"
            f"{PHARAOH_LINE}\n\n"
            f"{GOLD_DIAMOND} Ø§ÙÙØ¨ÙØº: <b>{fmt(amount)} {currency_name}</b>\n"
            f"{GOLD_DIAMOND} Ø§ÙÙØ¯Ø©: <b>{dur_text}</b>\n"
            f"{GOLD_DIAMOND} ÙØ³Ø¨Ø© Ø§ÙÙØ§Ø¦Ø¯Ø©: <b>{data['bank_rate']}%</b> Ø³ÙÙÙØ§Ù\n\n"
            f"ðµ Ø§ÙØ¹Ø§Ø¦Ø¯ Ø§ÙØ¥Ø¬ÙØ§ÙÙ: <b>{fmt(total_return)} {currency_name}</b>\n"
            f"ð·ï¸ Ø§ÙÙØ¨ÙØº Ø§ÙÙÙØ§Ø¦Ù: <b>{fmt(final)} {currency_name}</b>\n\n"
            f"{'â' * 20}\n"
            f"ð <b>ØªØ£Ø«ÙØ± Ø§ÙØªØ¶Ø®Ù</b> {inflation_source}\n"
            f"{'â' * 20}\n\n"
            f"ð» ÙØ³Ø¨Ø© Ø§ÙØªØ¶Ø®Ù: <b>{inflation_rate}%</b> Ø³ÙÙÙØ§Ù\n"
            f"ð¸ Ø®Ø³Ø§Ø±Ø© Ø§ÙÙÙØ© Ø§ÙØ´Ø±Ø§Ø¦ÙØ©: <b>{fmt(purchasing_loss)} {currency_name}</b>\n"
            f"â¨ Ø§ÙØ±Ø¨Ø­ Ø§ÙØ­ÙÙÙÙ: <b>{fmt(real_profit)} {currency_name}</b>\n\n"
        )
        result += _verdict(real_profit)

    # ââââââââ Ø°ÙØ¨ ââââââââ
    elif tool == "tool_gold":
        gold = live.get("gold")
        if not gold:
            await bot.send_message(chat_id, "â ØªØ¹Ø°Ø± Ø¬ÙØ¨ Ø£Ø³Ø¹Ø§Ø± Ø§ÙØ°ÙØ¨ Ø­Ø§ÙÙØ§Ù. Ø¬Ø±Ø¨ ØªØ§ÙÙ Ø¨Ø¹Ø¯ Ø´ÙÙØ©.")
            return

        current_price = gold["current_gram_local"]
        forecast_map = {"dur_6m": gold["forecast_6m"], "dur_1y": gold["forecast_1y"], "dur_3y": gold["forecast_3y"]}
        expected_price = forecast_map[dur_key]

        grams = amount / current_price
        future_value = grams * expected_price
        profit = future_value - amount
        real_profit = profit - purchasing_loss

        result = (
            f"<b>ð¥ ÙØªÙØ¬Ø© Ø§ÙØ§Ø³ØªØ«ÙØ§Ø± ÙÙ Ø§ÙØ°ÙØ¨</b>\n"
            f"{PHARAOH_LINE}\n\n"
            f"{GOLD_DIAMOND} Ø§ÙÙØ¨ÙØº: <b>{fmt(amount)} {currency_name}</b>\n"
            f"{GOLD_DIAMOND} Ø§ÙÙØ¯Ø©: <b>{dur_text}</b>\n\n"
            f"ð <b>Ø£Ø³Ø¹Ø§Ø± ÙØ­Ø¸ÙØ©:</b>\n"
            f"   Ø³Ø¹Ø± Ø§ÙØ¬Ø±Ø§Ù Ø§ÙØ¢Ù: <b>{fmt(current_price)} {currency_name}</b>\n"
            f"   (${fmt(gold['current_gram_usd'])} Ø¹Ø§ÙÙÙØ§Ù)\n\n"
            f"ð® <b>Ø§ÙØªÙÙØ¹Ø§Øª</b> (ÙÙÙ {gold['growth_rate']}% Ø³ÙÙÙØ§Ù):\n"
            f"   Ø§ÙØ³Ø¹Ø± Ø§ÙÙØªÙÙØ¹ Ø¨Ø¹Ø¯ {dur_text}: <b>{fmt(expected_price)} {currency_name}</b>\n\n"
            f"{'â' * 20}\n"
            f"âï¸ ÙØªØ´ØªØ±Ù: <b>{fmt(grams)} Ø¬Ø±Ø§Ù</b>\n"
            f"ðµ Ø§ÙÙÙÙØ© Ø§ÙÙØªÙÙØ¹Ø©: <b>{fmt(future_value)} {currency_name}</b>\n"
            f"ð Ø§ÙØ±Ø¨Ø­ Ø§ÙÙØªÙÙØ¹: <b>{fmt(profit)} {currency_name}</b>\n\n"
            f"{'â' * 20}\n"
            f"ð <b>ØªØ£Ø«ÙØ± Ø§ÙØªØ¶Ø®Ù</b> {inflation_source}\n"
            f"{'â' * 20}\n\n"
            f"ð» Ø§ÙØªØ¶Ø®Ù: <b>{inflation_rate}%</b> Ø³ÙÙÙØ§Ù\n"
            f"ð¸ Ø®Ø³Ø§Ø±Ø© Ø§ÙÙÙØ© Ø§ÙØ´Ø±Ø§Ø¦ÙØ©: <b>{fmt(purchasing_loss)} {currency_name}</b>\n"
            f"â¨ Ø§ÙØ±Ø¨Ø­ Ø§ÙØ­ÙÙÙÙ: <b>{fmt(real_profit)} {currency_name}</b>\n\n"
        )
        result += _verdict(real_profit)

    # ââââââââ Ø¯ÙÙØ§Ø± ââââââââ
    elif tool == "tool_usd":
        hc = live.get("hard_currency")
        if not hc:
            await bot.send_message(chat_id, "â ØªØ¹Ø°Ø± Ø¬ÙØ¨ Ø£Ø³Ø¹Ø§Ø± Ø§ÙØµØ±Ù Ø­Ø§ÙÙØ§Ù. Ø¬Ø±Ø¨ ØªØ§ÙÙ.")
            return

        current_rate = hc["current_rate"]
        forecast_map = {"dur_6m": hc["forecast_6m"], "dur_1y": hc["forecast_1y"], "dur_3y": hc["forecast_3y"]}
        expected_rate = forecast_map[dur_key]

        dollars = amount / current_rate
        future_value = dollars * expected_rate
        profit = future_value - amount
        real_profit = profit - purchasing_loss

        result = (
            f"<b>ðµ ÙØªÙØ¬Ø© Ø§ÙØ§Ø³ØªØ«ÙØ§Ø± ÙÙ Ø§ÙØ¯ÙÙØ§Ø±</b>\n"
            f"{PHARAOH_LINE}\n\n"
            f"{GOLD_DIAMOND} Ø§ÙÙØ¨ÙØº: <b>{fmt(amount)} {currency_name}</b>\n"
            f"{GOLD_DIAMOND} Ø§ÙÙØ¯Ø©: <b>{dur_text}</b>\n\n"
            f"ð <b>Ø³Ø¹Ø± ÙØ­Ø¸Ù:</b>\n"
            f"   Ø§ÙØ¯ÙÙØ§Ø± Ø§ÙØ¢Ù: <b>{fmt(current_rate)} {currency_name}</b>\n\n"
            f"ð® <b>Ø§ÙØªÙÙØ¹Ø§Øª</b> (ØªØºÙØ± {hc['change_rate']}% Ø³ÙÙÙØ§Ù):\n"
            f"   Ø§ÙØ³Ø¹Ø± Ø§ÙÙØªÙÙØ¹ Ø¨Ø¹Ø¯ {dur_text}: <b>{fmt(expected_rate)} {currency_name}</b>\n\n"
            f"{'â' * 20}\n"
            f"ð² ÙØªØ´ØªØ±Ù: <b>{fmt(dollars)} Ø¯ÙÙØ§Ø±</b>\n"
            f"ðµ Ø§ÙÙÙÙØ© Ø§ÙÙØªÙÙØ¹Ø©: <b>{fmt(future_value)} {currency_name}</b>\n"
            f"ð Ø§ÙØ±Ø¨Ø­ Ø§ÙÙØªÙÙØ¹: <b>{fmt(profit)} {currency_name}</b>\n\n"
            f"{'â' * 20}\n"
            f"ð <b>ØªØ£Ø«ÙØ± Ø§ÙØªØ¶Ø®Ù</b> {inflation_source}\n"
            f"{'â' * 20}\n\n"
            f"ð» Ø§ÙØªØ¶Ø®Ù: <b>{inflation_rate}%</b> Ø³ÙÙÙØ§Ù\n"
            f"ð¸ Ø®Ø³Ø§Ø±Ø© Ø§ÙÙÙØ© Ø§ÙØ´Ø±Ø§Ø¦ÙØ©: <b>{fmt(purchasing_loss)} {currency_name}</b>\n"
            f"â¨ Ø§ÙØ±Ø¨Ø­ Ø§ÙØ­ÙÙÙÙ: <b>{fmt(real_profit)} {currency_name}</b>\n\n"
        )
        result += _verdict(real_profit)

    result += f"\n<i>ð¢ Ø§ÙÙØªØ§Ø¦Ø¬ ØªÙØ¯ÙØ±ÙØ© ÙÙÙØ³Øª ÙØµÙØ­Ø© ÙØ§ÙÙØ©</i>"

    btns = await result_buttons()
    await send_logo(chat_id, result, reply_markup=btns)
    await state.clear()


def _verdict(real_profit: float) -> str:
    if real_profit > 0:
        return f"â <b>Ø§Ø³ØªØ«ÙØ§Ø±Ù ÙØªØºÙØ¨ Ø¹ÙÙ Ø§ÙØªØ¶Ø®Ù!</b> ð"
    else:
        return f"â ï¸ <b>Ø§Ø³ØªØ«ÙØ§Ø±Ù ÙØ§ ÙØªØºÙØ¨ Ø¹ÙÙ Ø§ÙØªØ¶Ø®Ù</b>"


# ââââââââââââââââââââââââââââââââââââââ
#           ÙÙØ­Ø© ØªØ­ÙÙ Ø§ÙØ£Ø¯ÙÙ
# ââââââââââââââââââââââââââââââââââââââ

@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()

    users = await get_users_count()
    settings = await get_all_settings()
    by_country = await get_users_by_country()

    country_stats = "\n".join(
        [f"   {c or 'ØºÙØ± ÙØ­Ø¯Ø¯'}: {n}" for c, n in by_country[:10]]
    ) if by_country else "   ÙØ§ ÙÙØ¬Ø¯"

    text = (
        f"<b>âï¸ ÙÙØ­Ø© ØªØ­ÙÙ Ø§ÙØ£Ø¯ÙÙ</b>\n"
        f"{PHARAOH_LINE}\n\n"
        f"ð¥ Ø§ÙÙØ³ØªØ®Ø¯ÙÙÙ: <b>{users}</b>\n"
        f"ð Ø­Ø³Ø¨ Ø§ÙØ¯ÙÙØ©:\n{country_stats}\n\n"
        f"<b>ð Ø§ÙØ¥Ø¹Ø¯Ø§Ø¯Ø§Øª:</b>\n"
        f"ð¥ ÙÙÙ Ø§ÙØ°ÙØ¨ Ø§ÙØ³ÙÙÙ: <b>{settings.get('gold_annual_growth', 10)}%</b>\n"
        f"ðµ ØªØºÙØ± Ø§ÙØ¹ÙÙØ© Ø§ÙØ³ÙÙÙ: <b>{settings.get('currency_annual_change', 8)}%</b>\n"
        f"ð ØªØ¶Ø®Ù Ø§ÙØªØ±Ø§Ø¶Ù: <b>{settings.get('fallback_inflation', 15)}%</b>\n"
        f"ð Ø±Ø§Ø¨Ø·: <a href=\"{settings.get('result_link_url', '#')}\">"
        f"{settings.get('result_link_text', 'Ø§ÙÙÙÙØ¹')}</a>\n"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ð¥ ÙÙÙ Ø§ÙØ°ÙØ¨ Ø§ÙØ³ÙÙÙ %", callback_data="edit_gold_annual_growth")],
        [InlineKeyboardButton(text="ðµ ØªØºÙØ± Ø§ÙØ¹ÙÙØ© Ø§ÙØ³ÙÙÙ %", callback_data="edit_currency_annual_change")],
        [InlineKeyboardButton(text="ð ØªØ¶Ø®Ù Ø§ÙØªØ±Ø§Ø¶Ù %", callback_data="edit_fallback_inflation")],
        [InlineKeyboardButton(text="ð ØªØ¹Ø¯ÙÙ Ø§ÙØ±Ø§Ø¨Ø·", callback_data="edit_result_link")],
        [InlineKeyboardButton(
            text="ð¢ Ø±Ø³Ø§ÙØ© Ø¬ÙØ§Ø¹ÙØ©",
            callback_data="admin_broadcast"
        )],
    ])

    await message.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML,
                         disable_web_page_preview=True)


@router.message(Command("myid"))
async def cmd_myid(message: Message):
    await message.answer(f"ð ÙØ¹Ø±ÙÙ: <code>{message.from_user.id}</code>",
                         parse_mode=ParseMode.HTML)


SETTING_LABELS = {
    "gold_annual_growth": "ÙØ³Ø¨Ø© ÙÙÙ Ø§ÙØ°ÙØ¨ Ø§ÙØ³ÙÙÙØ© %",
    "currency_annual_change": "ÙØ³Ø¨Ø© ØªØºÙØ± Ø§ÙØ¹ÙÙØ© Ø§ÙØ³ÙÙÙØ© %",
    "fallback_inflation": "ÙØ³Ø¨Ø© Ø§ÙØªØ¶Ø®Ù Ø§ÙØ§ÙØªØ±Ø§Ø¶ÙØ© %",
}


@router.callback_query(F.data.startswith("edit_"))
async def edit_setting(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return

    key = callback.data.replace("edit_", "")

    if key == "result_link":
        await state.set_state(AdminStates.waiting_link_text)
        await callback.message.answer(
            "ð <b>ØªØ¹Ø¯ÙÙ Ø§ÙØ±Ø§Ø¨Ø·</b>\n\nØ§ÙØªØ¨ ÙØµ Ø§ÙØ²Ø± Ø§ÙØ¬Ø¯ÙØ¯:",
            parse_mode=ParseMode.HTML
        )
        return

    if key not in SETTING_LABELS:
        return

    current = await get_setting(key)
    await state.update_data(editing_key=key)
    await state.set_state(AdminStates.waiting_setting_value)
    await callback.message.answer(
        f"âï¸ <b>{SETTING_LABELS[key]}</b>\n\n"
        f"Ø§ÙÙÙÙØ© Ø§ÙØ­Ø§ÙÙØ©: <b>{current}</b>\n\nØ§ÙØªØ¨ Ø§ÙÙÙÙØ© Ø§ÙØ¬Ø¯ÙØ¯Ø©:",
        parse_mode=ParseMode.HTML
    )


@router.message(AdminStates.waiting_setting_value)
async def save_setting_value(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        value = float(message.text.strip())
    except ValueError:
        await message.answer("â Ø£Ø¯Ø®Ù Ø±ÙÙ ØµØ­ÙØ­!")
        return

    data = await state.get_data()
    key = data["editing_key"]
    await set_setting(key, value)

    # ØªØ­Ø¯ÙØ« config Ø§ÙÙØ¨Ø§Ø´Ø± ÙÙ ÙØ­ØªØ§Ø¬
    import config
    if key == "gold_annual_growth":
        config.DEFAULT_GOLD_ANNUAL_GROWTH = value
    elif key == "currency_annual_change":
        config.DEFAULT_CURRENCY_ANNUAL_CHANGE = value

    await state.clear()
    await message.answer(
        f"â ØªÙ ØªØ¹Ø¯ÙÙ <b>{SETTING_LABELS[key]}</b> Ø¥ÙÙ: <b>{value}</b>\n\n/admin",
        parse_mode=ParseMode.HTML
    )


@router.message(AdminStates.waiting_link_text)
async def edit_link_text(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await set_setting("result_link_text", message.text.strip())
    await state.set_state(AdminStates.waiting_link_url)
    await message.answer("â Ø§ÙØ¢Ù Ø§ÙØªØ¨ Ø§ÙØ±Ø§Ø¨Ø· (URL):")


@router.message(AdminStates.waiting_link_url)
async def edit_link_url(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    url = message.text.strip()
    if not (url.startswith("http://") or url.startswith("https://") or url.startswith("tg://")):
        await message.answer("â Ø§ÙØ±Ø§Ø¨Ø· ÙØ§Ø²Ù ÙØ¨Ø¯Ø£ Ø¨Ù http:// Ø£Ù https://")
        return
    await set_setting("result_link_url", url)
    await state.clear()
    await message.answer("â ØªÙ ØªØ­Ø¯ÙØ« Ø§ÙØ±Ø§Ø¨Ø·!\n\n/admin")


# ââ Broadcast ââ

@router.callback_query(F.data == "admin_broadcast")
async def broadcast_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.waiting_broadcast_message)
    await callback.message.answer(
        "ð¢ <b>Ø±Ø³Ø§ÙØ© Ø¬ÙØ§Ø¹ÙØ©</b>\n\n"
        "Ø§ÙØªØ¨ Ø§ÙØ±Ø³Ø§ÙØ© (ÙØ¯Ø¹Ù HTML)\n/cancel ÙÙØ¥ÙØºØ§Ø¡",
        parse_mode=ParseMode.HTML
    )


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("â ØªÙ Ø§ÙØ¥ÙØºØ§Ø¡")


@router.message(AdminStates.waiting_broadcast_message)
async def broadcast_send(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    user_ids = await get_all_user_ids()
    total = len(user_ids)
    success = failed = 0

    status = await message.answer(f"ð¤ Ø¬Ø§Ø±Ù Ø§ÙØ¥Ø±Ø³Ø§Ù ÙÙ {total}...")

    for uid in user_ids:
        try:
            await bot.send_message(uid, message.text, parse_mode=ParseMode.HTML)
            success += 1
        except Exception:
            failed += 1
            await block_user(uid)
        if success % 25 == 0:
            await asyncio.sleep(1)

    await status.edit_text(
        f"â <b>ØªÙ Ø§ÙØ¥Ø±Ø³Ø§Ù</b>\n\nð Ø§ÙØ¥Ø¬ÙØ§ÙÙ: {total}\nâ ÙØ¬Ø§Ø­: {success}\nâ ÙØ´Ù: {failed}",
        parse_mode=ParseMode.HTML
    )


# ââ Fallback ââ

@router.message()
async def fallback(message: Message, state: FSMContext):
    current = await state.get_state()
    if current and "Admin" in current:
        return
    if current is None:
        is_sub = await check_subscription(message.from_user.id)
        if not is_sub:
            await message.answer("â ï¸ Ø§Ø´ØªØ±Ù ÙÙ Ø§ÙÙÙØ§Ø©!", reply_markup=sub_kb())
        else:
            await message.answer(f"Ø§ÙØªØ¨ /start Ø¹Ø´Ø§Ù ØªØ¨Ø¯Ø£ {ANKH}")


# ââââââââââââââââââââââââââââââââââââââ
#              Ø§ÙØªØ´ØºÙÙ
# ââââââââââââââââââââââââââââââââââââââ

async def on_startup(b: Bot):
    await init_db()
    if USE_WEBHOOK:
        await b.set_webhook(WEBHOOK_URL)
        logger.info(f"Webhook: {WEBHOOK_URL}")


async def on_shutdown(b: Bot):
    if USE_WEBHOOK:
        await b.delete_webhook()
    await b.session.close()


def main():
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    if USE_WEBHOOK:
        app = web.Application()
        handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
        handler.register(app, path=WEBHOOK_PATH)
        setup_application(app, dp, bot=bot)
        web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)
    else:
        asyncio.run(_poll(dp))


async def _poll(dp: Dispatcher):
    await init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    main()
