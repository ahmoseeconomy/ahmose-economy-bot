"""
ÃÂ¨ÃÂÃÂª ÃÂ§ÃÂÃÂªÃÂµÃÂ§ÃÂ¯ ÃÂ£ÃÂ­ÃÂÃÂ³ v2 - ÃÂ­ÃÂ§ÃÂ³ÃÂ¨ÃÂ© ÃÂ§ÃÂÃÂªÃÂ¶ÃÂ®ÃÂ ÃÂÃÂ§ÃÂÃÂ§ÃÂ³ÃÂªÃÂ«ÃÂÃÂ§ÃÂ±
=================================================
ÃÂ¨ÃÂÃÂ§ÃÂÃÂ§ÃÂª ÃÂÃÂ­ÃÂ¸ÃÂÃÂ© | ÃÂÃÂ ÃÂ¯ÃÂÃÂ ÃÂ§ÃÂÃÂ¹ÃÂ§ÃÂÃÂ | ÃÂ£ÃÂÃÂÃÂ§ÃÂ ÃÂÃÂ³ÃÂªÃÂÃÂ­ÃÂ§ÃÂ© ÃÂÃÂ ÃÂ§ÃÂÃÂÃÂÃÂ¬ÃÂ
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


# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
#              ÃÂ­ÃÂ§ÃÂÃÂ§ÃÂª FSM
# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ

class InvestForm(StatesGroup):
    waiting_country = State()
    waiting_amount = State()
    waiting_duration = State()
    waiting_tool = State()
    waiting_bank_rate = State()  # ÃÂ§ÃÂÃÂÃÂ³ÃÂªÃÂ®ÃÂ¯ÃÂ ÃÂÃÂ¯ÃÂ®ÃÂ ÃÂÃÂ³ÃÂ¨ÃÂ© ÃÂ§ÃÂÃÂ´ÃÂÃÂ§ÃÂ¯ÃÂ©


class AdminStates(StatesGroup):
    waiting_setting_value = State()
    waiting_broadcast_message = State()
    waiting_link_text = State()
    waiting_link_url = State()


# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
#              ÃÂ£ÃÂ¯ÃÂÃÂ§ÃÂª ÃÂÃÂ³ÃÂ§ÃÂ¹ÃÂ¯ÃÂ©
# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ

# Ã¢ÂÂÃ¢ÂÂ ÃÂ£ÃÂÃÂÃÂ§ÃÂ ÃÂÃÂ³ÃÂªÃÂÃÂ­ÃÂ§ÃÂ© ÃÂÃÂ ÃÂ§ÃÂÃÂÃÂÃÂ¬ÃÂ (ÃÂÃÂÃÂ§ÃÂ³ÃÂªÃÂ®ÃÂ¯ÃÂ§ÃÂ ÃÂÃÂ ÃÂ§ÃÂÃÂ±ÃÂ³ÃÂ§ÃÂ¦ÃÂ) Ã¢ÂÂÃ¢ÂÂ
# ÃÂ°ÃÂÃÂ¨ÃÂ Ã¢ÂÂÃ¯Â¸Â | ÃÂ£ÃÂ³ÃÂÃÂ¯ Ã°ÂÂÂ¤ | ÃÂ£ÃÂ²ÃÂ±ÃÂ ÃÂ³ÃÂÃÂ§ÃÂ Ã°ÂÂÂ· | ÃÂ±ÃÂÃÂ§ÃÂ¯ÃÂ Ã¢ÂÂÃ¯Â¸Â
# ÃÂÃÂ³ÃÂªÃÂ®ÃÂ¯ÃÂ ÃÂ¥ÃÂÃÂÃÂÃÂ¬ÃÂ ÃÂ°ÃÂÃÂ¨ÃÂÃÂ© + ÃÂ®ÃÂ·ÃÂÃÂ· ÃÂÃÂ±ÃÂ¹ÃÂÃÂÃÂÃÂ©

PHARAOH_LINE = "Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ"
GOLD_DIAMOND = "Ã¢ÂÂ"
ANKH = "Ã¢ÂÂ¥"

def fmt(n: float) -> str:
    if n == int(n):
        return f"{int(n):,}"
    return f"{n:,.2f}"


async def check_subscription(user_id: int) -> bool:
    # TODO: re-enable after testing
    return True


def sub_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Ã°ÂÂÂ¢ ÃÂ§ÃÂ´ÃÂªÃÂ±ÃÂ ÃÂÃÂ ÃÂ§ÃÂÃÂÃÂÃÂ§ÃÂ©", url=CHANNEL_LINK)],
        [InlineKeyboardButton(text=f"{ANKH} ÃÂªÃÂ­ÃÂÃÂÃÂª ÃÂÃÂ ÃÂ§ÃÂÃÂ§ÃÂ´ÃÂªÃÂ±ÃÂ§ÃÂ", callback_data="check_sub")]
    ])


async def send_logo(chat_id: int, caption: str, reply_markup=None):
    """ÃÂ¥ÃÂ±ÃÂ³ÃÂ§ÃÂ ÃÂ§ÃÂÃÂÃÂÃÂ¬ÃÂ ÃÂÃÂ¹ ÃÂ±ÃÂ³ÃÂ§ÃÂÃÂ©"""
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
        [InlineKeyboardButton(text=f"Ã°ÂÂÂ {link_text}", url=link_url)],
        [InlineKeyboardButton(text=f"{ANKH} ÃÂ­ÃÂ³ÃÂ§ÃÂ¨ ÃÂ¬ÃÂ¯ÃÂÃÂ¯", callback_data="new_calc")]
    ])


def is_admin(uid: int) -> bool:
    return uid in ADMIN_IDS


def country_keyboard(page: int = 0) -> InlineKeyboardMarkup:
    """ÃÂ£ÃÂ²ÃÂ±ÃÂ§ÃÂ± ÃÂ§ÃÂ®ÃÂªÃÂÃÂ§ÃÂ± ÃÂ§ÃÂÃÂ¯ÃÂÃÂÃÂ© ÃÂÃÂ¹ ÃÂ³ÃÂÃÂ±ÃÂÃÂ"""
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

    # ÃÂ£ÃÂ²ÃÂ±ÃÂ§ÃÂ± ÃÂ§ÃÂÃÂªÃÂÃÂÃÂ
    nav = []
    if has_prev:
        nav.append(InlineKeyboardButton(text="Ã¢ÂÂÃ¯Â¸Â ÃÂ§ÃÂÃÂ³ÃÂ§ÃÂ¨ÃÂ", callback_data=f"cpage_{page-1}"))
    nav.append(InlineKeyboardButton(text=f"Ã°ÂÂÂ {page+1}", callback_data="noop"))
    if has_next:
        nav.append(InlineKeyboardButton(text="ÃÂ§ÃÂÃÂªÃÂ§ÃÂÃÂ Ã¢ÂÂ¶Ã¯Â¸Â", callback_data=f"cpage_{page+1}"))
    rows.append(nav)

    return InlineKeyboardMarkup(inline_keyboard=rows)


def search_results_keyboard(results: list) -> InlineKeyboardMarkup:
    """ÃÂ£ÃÂ²ÃÂ±ÃÂ§ÃÂ± ÃÂÃÂªÃÂ§ÃÂ¦ÃÂ¬ ÃÂ§ÃÂÃÂ¨ÃÂ­ÃÂ«"""
    rows = []
    for c in results:
        rows.append([InlineKeyboardButton(
            text=f"{c['flag']} {c['name_ar']} ({c['currency']})",
            callback_data=f"country_{c['code']}"
        )])
    rows.append([InlineKeyboardButton(text="Ã°ÂÂÂ ÃÂ¹ÃÂ±ÃÂ¶ ÃÂÃÂ ÃÂ§ÃÂÃÂ¯ÃÂÃÂ", callback_data="cpage_0")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def duration_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="6Ã¯Â¸ÂÃ¢ÂÂ£ ÃÂ´ÃÂÃÂÃÂ±", callback_data="dur_6m"),
        InlineKeyboardButton(text="1Ã¯Â¸ÂÃ¢ÂÂ£ ÃÂ³ÃÂÃÂ©", callback_data="dur_1y"),
        InlineKeyboardButton(text="3Ã¯Â¸ÂÃ¢ÂÂ£ ÃÂ³ÃÂÃÂÃÂ§ÃÂª", callback_data="dur_3y"),
    ]])


def tool_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Ã°ÂÂÂ¦ ÃÂ´ÃÂÃÂ§ÃÂ¯ÃÂ§ÃÂª ÃÂ¨ÃÂÃÂÃÂÃÂ©", callback_data="tool_bank")],
        [InlineKeyboardButton(text=f"Ã°ÂÂ¥Â ÃÂ°ÃÂÃÂ¨ (ÃÂ³ÃÂ¹ÃÂ± ÃÂÃÂ­ÃÂ¸ÃÂ)", callback_data="tool_gold")],
        [InlineKeyboardButton(text="Ã°ÂÂÂµ ÃÂ¹ÃÂÃÂÃÂ© ÃÂµÃÂ¹ÃÂ¨ÃÂ© (ÃÂ¯ÃÂÃÂÃÂ§ÃÂ±)", callback_data="tool_usd")],
    ])


# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
#           ÃÂ£ÃÂÃÂ§ÃÂÃÂ± ÃÂ§ÃÂÃÂÃÂ³ÃÂªÃÂ®ÃÂ¯ÃÂ
# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ

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
            f"<b>{GOLD_DIAMOND} ÃÂ­ÃÂ§ÃÂ³ÃÂ¨ ÃÂ¹ÃÂÃÂ ÃÂÃÂÃÂÃÂ³ÃÂ {GOLD_DIAMOND}</b>\n"
            f"{PHARAOH_LINE}\n\n"
            "ÃÂ§ÃÂÃÂªÃÂ¶ÃÂ®ÃÂ ÃÂÃÂ´ ÃÂ¨ÃÂÃÂ³ÃÂªÃÂÃÂ ÃÂ­ÃÂ¯\n"
            "ÃÂ§ÃÂ¹ÃÂ±ÃÂ ÃÂ¯ÃÂÃÂÃÂÃÂªÃÂ: ÃÂ§ÃÂ³ÃÂªÃÂ«ÃÂÃÂ§ÃÂ±ÃÂ ÃÂ¨ÃÂÃÂÃÂ³ÃÂ¨\n"
            "ÃÂÃÂÃÂ§ ÃÂ¨ÃÂÃÂ®ÃÂ³ÃÂ± ÃÂÃÂ ÃÂºÃÂÃÂ± ÃÂÃÂ§ ÃÂªÃÂ­ÃÂ³ÃÂ Ã¢ÂÂ¡\n\n"
            "Ã¢ÂÂ Ã¯Â¸Â ÃÂÃÂ§ÃÂ²ÃÂ ÃÂªÃÂÃÂÃÂ ÃÂÃÂ´ÃÂªÃÂ±ÃÂ ÃÂÃÂ ÃÂ§ÃÂÃÂÃÂÃÂ§ÃÂ© ÃÂ§ÃÂÃÂ£ÃÂÃÂ\n\n"
            "Ã°ÂÂÂ¢ ÃÂ§ÃÂ´ÃÂªÃÂ±ÃÂ ÃÂÃÂ¨ÃÂ¹ÃÂ¯ÃÂÃÂ ÃÂ§ÃÂ¶ÃÂºÃÂ· ÃÂªÃÂ­ÃÂÃÂ Ã°ÂÂÂ",
            reply_markup=sub_kb()
        )
        return

    await ask_country(message.chat.id, state)


async def ask_country(chat_id: int, state: FSMContext):
    """ÃÂ³ÃÂ¤ÃÂ§ÃÂ ÃÂ§ÃÂÃÂÃÂ³ÃÂªÃÂ®ÃÂ¯ÃÂ ÃÂ¹ÃÂ ÃÂ¨ÃÂÃÂ¯ÃÂ"""
    await state.set_state(InvestForm.waiting_country)
    await send_logo(
        chat_id,
        f"<b>{GOLD_DIAMOND} ÃÂ­ÃÂ§ÃÂ³ÃÂ¨ÃÂ© ÃÂ§ÃÂÃÂªÃÂ¶ÃÂ®ÃÂ ÃÂÃÂ§ÃÂÃÂ§ÃÂ³ÃÂªÃÂ«ÃÂÃÂ§ÃÂ± {GOLD_DIAMOND}</b>\n"
        f"{PHARAOH_LINE}\n\n"
        "Ã°ÂÂÂ <b>ÃÂ§ÃÂ®ÃÂªÃÂ§ÃÂ± ÃÂ¨ÃÂÃÂ¯ÃÂ</b> ÃÂ¹ÃÂ´ÃÂ§ÃÂ ÃÂÃÂ¬ÃÂÃÂ¨ÃÂÃÂ ÃÂ§ÃÂÃÂ£ÃÂ³ÃÂ¹ÃÂ§ÃÂ± ÃÂ§ÃÂÃÂÃÂ­ÃÂ¸ÃÂÃÂ©\n\n"
        "Ã¢ÂÂÃ¯Â¸Â <b>ÃÂ§ÃÂÃÂªÃÂ¨ ÃÂ§ÃÂ³ÃÂ ÃÂ¨ÃÂÃÂ¯ÃÂ</b> (ÃÂ¹ÃÂ±ÃÂ¨ÃÂ ÃÂ£ÃÂ ÃÂ¥ÃÂÃÂ¬ÃÂÃÂÃÂ²ÃÂ)\n"
        "ÃÂ£ÃÂ ÃÂ§ÃÂ®ÃÂªÃÂ§ÃÂ± ÃÂÃÂ ÃÂ§ÃÂÃÂÃÂ§ÃÂ¦ÃÂÃÂ© Ã°ÂÂÂ",
        reply_markup=country_keyboard(0)
    )


@router.callback_query(F.data == "check_sub")
async def check_sub_cb(callback: CallbackQuery, state: FSMContext):
    is_sub = await check_subscription(callback.from_user.id)
    if is_sub:
        await callback.message.delete()
        await ask_country(callback.message.chat.id, state)
    else:
        await callback.answer("Ã¢ÂÂ ÃÂÃÂ³ÃÂ ÃÂÃÂ´ÃÂªÃÂ±ÃÂ! ÃÂ§ÃÂ´ÃÂªÃÂ±ÃÂ ÃÂ§ÃÂÃÂ£ÃÂÃÂ", show_alert=True)


@router.callback_query(F.data == "new_calc")
async def new_calc_cb(callback: CallbackQuery, state: FSMContext):
    is_sub = await check_subscription(callback.from_user.id)
    if not is_sub:
        await callback.message.answer("Ã¢ÂÂ Ã¯Â¸Â ÃÂ§ÃÂ´ÃÂªÃÂ±ÃÂ ÃÂÃÂ ÃÂ§ÃÂÃÂÃÂÃÂ§ÃÂ© ÃÂ§ÃÂÃÂ£ÃÂÃÂ!", reply_markup=sub_kb())
        return
    await ask_country(callback.message.chat.id, state)


# Ã¢ÂÂÃ¢ÂÂ ÃÂªÃÂµÃÂÃÂ­ ÃÂ§ÃÂÃÂ¯ÃÂÃÂ Ã¢ÂÂÃ¢ÂÂ

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


# Ã¢ÂÂÃ¢ÂÂ ÃÂ§ÃÂÃÂ¨ÃÂ­ÃÂ« ÃÂ¹ÃÂ ÃÂ§ÃÂÃÂ¯ÃÂÃÂÃÂ© ÃÂ¨ÃÂ§ÃÂÃÂÃÂªÃÂ§ÃÂ¨ÃÂ© Ã¢ÂÂÃ¢ÂÂ
@router.message(InvestForm.waiting_country)
async def search_country_text(message: Message, state: FSMContext):
    """ÃÂ§ÃÂÃÂÃÂ³ÃÂªÃÂ®ÃÂ¯ÃÂ ÃÂÃÂªÃÂ¨ ÃÂ§ÃÂ³ÃÂ ÃÂ¨ÃÂÃÂ¯ÃÂ ÃÂ¨ÃÂ¯ÃÂ ÃÂÃÂ§ ÃÂÃÂ¶ÃÂºÃÂ· ÃÂ²ÃÂ±"""
    query = message.text.strip()
    results = search_countries(query, limit=6)

    if not results:
        await message.answer(
            f"Ã¢ÂÂ ÃÂÃÂÃÂÃÂ´ ÃÂ¯ÃÂÃÂÃÂ© ÃÂ§ÃÂ³ÃÂÃÂÃÂ§ <b>{query}</b>\n\n"
            "ÃÂ¬ÃÂ±ÃÂ¨ ÃÂªÃÂÃÂªÃÂ¨ ÃÂ§ÃÂ³ÃÂ ÃÂªÃÂ§ÃÂÃÂ ÃÂ£ÃÂ ÃÂ§ÃÂ®ÃÂªÃÂ§ÃÂ± ÃÂÃÂ ÃÂ§ÃÂÃÂÃÂ§ÃÂ¦ÃÂÃÂ© Ã°ÂÂÂ",
            parse_mode=ParseMode.HTML,
            reply_markup=country_keyboard(0)
        )
        return

    if len(results) == 1:
        # ÃÂÃÂªÃÂÃÂ¬ÃÂ© ÃÂÃÂ§ÃÂ­ÃÂ¯ÃÂ© Ã¢ÂÂ ÃÂ§ÃÂ®ÃÂªÃÂ§ÃÂ±ÃÂÃÂ§ ÃÂÃÂ¨ÃÂ§ÃÂ´ÃÂ±ÃÂ©
        country = results[0]
        await _select_country(message.chat.id, message.from_user, country, state)
        return

    # ÃÂ£ÃÂÃÂ«ÃÂ± ÃÂÃÂ ÃÂÃÂªÃÂÃÂ¬ÃÂ© Ã¢ÂÂ ÃÂ¹ÃÂ±ÃÂ¶ÃÂÃÂ§ ÃÂÃÂ£ÃÂ²ÃÂ±ÃÂ§ÃÂ±
    await message.answer(
        f"Ã°ÂÂÂ ÃÂÃÂªÃÂ§ÃÂ¦ÃÂ¬ ÃÂ§ÃÂÃÂ¨ÃÂ­ÃÂ« ÃÂ¹ÃÂ <b>{query}</b>:",
        parse_mode=ParseMode.HTML,
        reply_markup=search_results_keyboard(results)
    )


# Ã¢ÂÂÃ¢ÂÂ ÃÂ§ÃÂ®ÃÂªÃÂÃÂ§ÃÂ± ÃÂ§ÃÂÃÂ¯ÃÂÃÂÃÂ© Ã¢ÂÂÃ¢ÂÂ

@router.callback_query(F.data.startswith("country_"), InvestForm.waiting_country)
async def select_country_cb(callback: CallbackQuery, state: FSMContext):
    code = callback.data.replace("country_", "")
    country = get_country_by_code(code)
    if not country:
        await callback.answer("Ã¢ÂÂ ÃÂ®ÃÂ·ÃÂ£", show_alert=True)
        return
    try:
        await callback.message.delete()
    except Exception:
        pass
    await _select_country(callback.message.chat.id, callback.from_user, country, state)


async def _select_country(chat_id: int, user, country: dict, state: FSMContext):
    """ÃÂÃÂ¹ÃÂ§ÃÂÃÂ¬ÃÂ© ÃÂ§ÃÂ®ÃÂªÃÂÃÂ§ÃÂ± ÃÂ§ÃÂÃÂ¯ÃÂÃÂÃÂ© (ÃÂÃÂ´ÃÂªÃÂ±ÃÂÃÂ© ÃÂ¨ÃÂÃÂ ÃÂ§ÃÂÃÂ¶ÃÂºÃÂ· ÃÂÃÂ§ÃÂÃÂÃÂªÃÂ§ÃÂ¨ÃÂ©)"""
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
        f"Ã¢ÂÂ³ ÃÂ¬ÃÂ§ÃÂ±ÃÂ ÃÂ¬ÃÂÃÂ¨ ÃÂ§ÃÂÃÂ¨ÃÂÃÂ§ÃÂÃÂ§ÃÂª ÃÂ§ÃÂÃÂÃÂ­ÃÂ¸ÃÂÃÂ© ÃÂÃÂ {country['flag']} {country['name_ar']}..."
    )

    live_data = await fetch_all_data(country["code"], country["currency"])
    await state.update_data(country=country, live_data=live_data)

    summary = f"<b>{GOLD_DIAMOND} {country['flag']} ÃÂ£ÃÂ³ÃÂ¹ÃÂ§ÃÂ± {country['name_ar']} ÃÂ§ÃÂÃÂÃÂ­ÃÂ¸ÃÂÃÂ© {GOLD_DIAMOND}</b>\n"
    summary += f"{PHARAOH_LINE}\n\n"

    if live_data["gold"]:
        g = live_data["gold"]
        summary += f"Ã°ÂÂ¥Â <b>ÃÂ§ÃÂÃÂ°ÃÂÃÂ¨:</b> {fmt(g['current_gram_local'])} {country['currency_name']}/ÃÂ¬ÃÂ±ÃÂ§ÃÂ\n"
        summary += f"   <i>(${fmt(g['current_gram_usd'])} ÃÂ¹ÃÂ§ÃÂÃÂÃÂÃÂ§ÃÂ)</i>\n\n"

    if live_data["hard_currency"]:
        h = live_data["hard_currency"]
        summary += f"Ã°ÂÂÂµ <b>ÃÂ§ÃÂÃÂ¯ÃÂÃÂÃÂ§ÃÂ±:</b> {fmt(h['current_rate'])} {country['currency_name']}\n\n"

    if live_data["inflation"]:
        inf_data = live_data["inflation"]
        summary += f"Ã°ÂÂÂ <b>ÃÂ§ÃÂÃÂªÃÂ¶ÃÂ®ÃÂ:</b> {inf_data['rate']}% <i>(ÃÂ¢ÃÂ®ÃÂ± ÃÂ¨ÃÂÃÂ§ÃÂÃÂ§ÃÂª: {inf_data['year']} - {inf_data['source']})</i>\n\n"
    else:
        fb = await get_setting("fallback_inflation")
        summary += f"Ã°ÂÂÂ <b>ÃÂ§ÃÂÃÂªÃÂ¶ÃÂ®ÃÂ:</b> {fb}% <i>(ÃÂªÃÂÃÂ¯ÃÂÃÂ±ÃÂ)</i>\n\n"

    summary += f"{PHARAOH_LINE}\n"
    summary += "Ã°ÂÂÂ° <b>ÃÂ§ÃÂÃÂªÃÂ¨ ÃÂ§ÃÂÃÂÃÂ¨ÃÂÃÂº ÃÂ§ÃÂÃÂÃÂ ÃÂ¹ÃÂ§ÃÂÃÂ² ÃÂªÃÂ³ÃÂªÃÂ«ÃÂÃÂ±ÃÂ</b>\n"
    summary += f"<i>(ÃÂ£ÃÂ±ÃÂÃÂ§ÃÂ ÃÂÃÂÃÂ· ÃÂ¨ÃÂ {country['currency_name']})</i>"

    await state.set_state(InvestForm.waiting_amount)
    try:
        await loading.delete()
    except Exception:
        pass
    await bot.send_message(chat_id, summary, parse_mode=ParseMode.HTML)


# Ã¢ÂÂÃ¢ÂÂ ÃÂ¥ÃÂ¯ÃÂ®ÃÂ§ÃÂ ÃÂ§ÃÂÃÂÃÂ¨ÃÂÃÂº Ã¢ÂÂÃ¢ÂÂ

@router.message(InvestForm.waiting_amount)
async def receive_amount(message: Message, state: FSMContext):
    text = message.text.strip().replace(",", "").replace("ÃÂ¬", "").replace("ÃÂ", "")
    try:
        amount = float(text)
        if amount <= 0:
            raise ValueError
        if amount > 999_999_999_999:
            await message.answer("Ã¢ÂÂ Ã¯Â¸Â ÃÂ§ÃÂÃÂÃÂ¨ÃÂÃÂº ÃÂÃÂ¨ÃÂÃÂ± ÃÂ£ÃÂÃÂ!")
            return
    except (ValueError, TypeError):
        await message.answer(
            "Ã¢ÂÂ <b>ÃÂ¥ÃÂ¯ÃÂ®ÃÂ§ÃÂ ÃÂºÃÂÃÂ± ÃÂµÃÂ­ÃÂÃÂ­</b>\n\nÃÂ§ÃÂÃÂªÃÂ¨ ÃÂ£ÃÂ±ÃÂÃÂ§ÃÂ ÃÂÃÂÃÂ·\nÃÂÃÂ«ÃÂ§ÃÂ: <code>100000</code>",
            parse_mode=ParseMode.HTML
        )
        return

    data = await state.get_data()
    country = data["country"]
    await state.update_data(amount=amount)
    await state.set_state(InvestForm.waiting_duration)
    await message.answer(
        f"Ã°ÂÂÂ° ÃÂ§ÃÂÃÂÃÂ¨ÃÂÃÂº: <b>{fmt(amount)} {country['currency_name']}</b>\n\n"
        "Ã¢ÂÂ³ ÃÂ§ÃÂ®ÃÂªÃÂ§ÃÂ± ÃÂÃÂ¯ÃÂ© ÃÂ§ÃÂÃÂ§ÃÂ³ÃÂªÃÂ«ÃÂÃÂ§ÃÂ± Ã°ÂÂÂ",
        reply_markup=duration_kb(),
        parse_mode=ParseMode.HTML
    )


# Ã¢ÂÂÃ¢ÂÂ ÃÂ§ÃÂ®ÃÂªÃÂÃÂ§ÃÂ± ÃÂ§ÃÂÃÂÃÂ¯ÃÂ© Ã¢ÂÂÃ¢ÂÂ

@router.callback_query(F.data.startswith("dur_"), InvestForm.waiting_duration)
async def receive_duration(callback: CallbackQuery, state: FSMContext):
    dur_map = {"dur_6m": ("6 ÃÂ´ÃÂÃÂÃÂ±", 0.5), "dur_1y": ("ÃÂ³ÃÂÃÂ©", 1.0), "dur_3y": ("3 ÃÂ³ÃÂÃÂÃÂ§ÃÂª", 3.0)}
    dur_text, dur_years = dur_map[callback.data]

    await state.update_data(duration_text=dur_text, duration_years=dur_years, dur_key=callback.data)
    await state.set_state(InvestForm.waiting_tool)

    data = await state.get_data()
    country = data["country"]
    await callback.message.edit_text(
        f"Ã°ÂÂÂ° ÃÂ§ÃÂÃÂÃÂ¨ÃÂÃÂº: <b>{fmt(data['amount'])} {country['currency_name']}</b>\n"
        f"Ã¢ÂÂ³ ÃÂ§ÃÂÃÂÃÂ¯ÃÂ©: <b>{dur_text}</b>\n\n"
        "Ã°ÂÂÂ ÃÂ§ÃÂ®ÃÂªÃÂ§ÃÂ± ÃÂ£ÃÂ¯ÃÂ§ÃÂ© ÃÂ§ÃÂÃÂ§ÃÂ³ÃÂªÃÂ«ÃÂÃÂ§ÃÂ± Ã°ÂÂÂ",
        reply_markup=tool_kb(),
        parse_mode=ParseMode.HTML
    )


# Ã¢ÂÂÃ¢ÂÂ ÃÂ§ÃÂ®ÃÂªÃÂÃÂ§ÃÂ± ÃÂ§ÃÂÃÂ£ÃÂ¯ÃÂ§ÃÂ© Ã¢ÂÂÃ¢ÂÂ

@router.callback_query(F.data.startswith("tool_"), InvestForm.waiting_tool)
async def receive_tool(callback: CallbackQuery, state: FSMContext):
    tool = callback.data

    if tool == "tool_bank":
        # ÃÂ§ÃÂÃÂ´ÃÂÃÂ§ÃÂ¯ÃÂ©: ÃÂ§ÃÂÃÂÃÂ³ÃÂªÃÂ®ÃÂ¯ÃÂ ÃÂÃÂ¯ÃÂ®ÃÂ ÃÂÃÂ³ÃÂ¨ÃÂ© ÃÂ§ÃÂÃÂÃÂ§ÃÂ¦ÃÂ¯ÃÂ© ÃÂ¨ÃÂÃÂÃÂ³ÃÂ
        await state.update_data(tool=tool)
        await state.set_state(InvestForm.waiting_bank_rate)
        await callback.message.edit_text(
            "Ã°ÂÂÂ¦ <b>ÃÂ´ÃÂÃÂ§ÃÂ¯ÃÂ§ÃÂª ÃÂ¨ÃÂÃÂÃÂÃÂ©</b>\n"
            f"{PHARAOH_LINE}\n\n"
            "Ã°ÂÂÂ <b>ÃÂ§ÃÂÃÂªÃÂ¨ ÃÂÃÂ³ÃÂ¨ÃÂ© ÃÂ§ÃÂÃÂÃÂ§ÃÂ¦ÃÂ¯ÃÂ© ÃÂ§ÃÂÃÂ³ÃÂÃÂÃÂÃÂ© ÃÂÃÂ´ÃÂÃÂ§ÃÂ¯ÃÂªÃÂ</b>\n"
            "<i>(ÃÂ±ÃÂÃÂ ÃÂÃÂÃÂ· - ÃÂÃÂ«ÃÂ§ÃÂ: 27)</i>\n\n"
            "Ã°ÂÂÂ¡ ÃÂ§ÃÂÃÂÃÂ³ÃÂ¨ÃÂ© ÃÂ¨ÃÂªÃÂ®ÃÂªÃÂÃÂ ÃÂ­ÃÂ³ÃÂ¨ ÃÂ§ÃÂÃÂ¨ÃÂÃÂ ÃÂÃÂÃÂÃÂ¹ ÃÂ§ÃÂÃÂ´ÃÂÃÂ§ÃÂ¯ÃÂ©",
            parse_mode=ParseMode.HTML
        )
        return

    # ÃÂ§ÃÂÃÂ°ÃÂÃÂ¨ ÃÂÃÂ§ÃÂÃÂ¯ÃÂÃÂÃÂ§ÃÂ±: ÃÂ­ÃÂ³ÃÂ§ÃÂ¨ ÃÂÃÂ¨ÃÂ§ÃÂ´ÃÂ±
    await state.update_data(tool=tool)
    await calculate_result(callback, state)


# Ã¢ÂÂÃ¢ÂÂ ÃÂ¥ÃÂ¯ÃÂ®ÃÂ§ÃÂ ÃÂÃÂ³ÃÂ¨ÃÂ© ÃÂ§ÃÂÃÂ´ÃÂÃÂ§ÃÂ¯ÃÂ© ÃÂ§ÃÂÃÂ¨ÃÂÃÂÃÂÃÂ© Ã¢ÂÂÃ¢ÂÂ

@router.message(InvestForm.waiting_bank_rate)
async def receive_bank_rate(message: Message, state: FSMContext):
    try:
        rate = float(message.text.strip().replace("%", ""))
        if rate <= 0 or rate > 100:
            raise ValueError
    except (ValueError, TypeError):
        await message.answer("Ã¢ÂÂ ÃÂ§ÃÂÃÂªÃÂ¨ ÃÂÃÂ³ÃÂ¨ÃÂ© ÃÂµÃÂ­ÃÂÃÂ­ÃÂ© (ÃÂÃÂ«ÃÂ§ÃÂ: 27)")
        return

    await state.update_data(bank_rate=rate)

    # ÃÂÃÂ­ÃÂ§ÃÂÃÂ callback ÃÂ¹ÃÂ´ÃÂ§ÃÂ ÃÂÃÂ³ÃÂªÃÂ®ÃÂ¯ÃÂ ÃÂÃÂÃÂ³ ÃÂ§ÃÂÃÂ¯ÃÂ§ÃÂÃÂ©
    data = await state.get_data()
    await calculate_and_send(message.chat.id, data, state)


# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
#           ÃÂ­ÃÂ³ÃÂ§ÃÂ¨ ÃÂ§ÃÂÃÂÃÂªÃÂÃÂ¬ÃÂ©
# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ

async def calculate_result(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await callback.message.edit_text("Ã¢ÂÂ³ ÃÂ¬ÃÂ§ÃÂ±ÃÂ ÃÂ§ÃÂÃÂ­ÃÂ³ÃÂ§ÃÂ¨...")
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

    # Ã¢ÂÂÃ¢ÂÂ ÃÂ§ÃÂÃÂªÃÂ¶ÃÂ®ÃÂ Ã¢ÂÂÃ¢ÂÂ
    if live["inflation"]:
        inflation_rate = live["inflation"]["rate"]
        inflation_source = f"({live['inflation']['source']} - {live['inflation']['year']})"
    else:
        inflation_rate = await get_setting("fallback_inflation")
        inflation_source = "(ÃÂªÃÂÃÂ¯ÃÂÃÂ±ÃÂ)"

    inf = inflation_rate / 100
    purchasing_loss = amount * (1 - (1 / ((1 + inf) ** dur_years)))

    result = ""

    # Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ ÃÂ´ÃÂÃÂ§ÃÂ¯ÃÂ§ÃÂª ÃÂ¨ÃÂÃÂÃÂÃÂ© Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
    if tool == "tool_bank":
        rate = data["bank_rate"] / 100
        total_return = amount * rate * dur_years
        final = amount + total_return
        real_profit = total_return - purchasing_loss

        result = (
            f"<b>Ã°ÂÂÂ¦ ÃÂÃÂªÃÂÃÂ¬ÃÂ© ÃÂ§ÃÂÃÂ§ÃÂ³ÃÂªÃÂ«ÃÂÃÂ§ÃÂ± ÃÂÃÂ ÃÂ´ÃÂÃÂ§ÃÂ¯ÃÂ§ÃÂª ÃÂ¨ÃÂÃÂÃÂÃÂ©</b>\n"
            f"{PHARAOH_LINE}\n\n"
            f"{GOLD_DIAMOND} ÃÂ§ÃÂÃÂÃÂ¨ÃÂÃÂº: <b>{fmt(amount)} {currency_name}</b>\n"
            f"{GOLD_DIAMOND} ÃÂ§ÃÂÃÂÃÂ¯ÃÂ©: <b>{dur_text}</b>\n"
            f"{GOLD_DIAMOND} ÃÂÃÂ³ÃÂ¨ÃÂ© ÃÂ§ÃÂÃÂÃÂ§ÃÂ¦ÃÂ¯ÃÂ©: <b>{data['bank_rate']}%</b> ÃÂ³ÃÂÃÂÃÂÃÂ§ÃÂ\n\n"
            f"Ã°ÂÂÂµ ÃÂ§ÃÂÃÂ¹ÃÂ§ÃÂ¦ÃÂ¯ ÃÂ§ÃÂÃÂ¥ÃÂ¬ÃÂÃÂ§ÃÂÃÂ: <b>{fmt(total_return)} {currency_name}</b>\n"
            f"Ã°ÂÂÂ·Ã¯Â¸Â ÃÂ§ÃÂÃÂÃÂ¨ÃÂÃÂº ÃÂ§ÃÂÃÂÃÂÃÂ§ÃÂ¦ÃÂ: <b>{fmt(final)} {currency_name}</b>\n\n"
            f"{'Ã¢ÂÂ' * 20}\n"
            f"Ã°ÂÂÂ <b>ÃÂªÃÂ£ÃÂ«ÃÂÃÂ± ÃÂ§ÃÂÃÂªÃÂ¶ÃÂ®ÃÂ</b> {inflation_source}\n"
            f"{'Ã¢ÂÂ' * 20}\n\n"
            f"Ã°ÂÂÂ» ÃÂÃÂ³ÃÂ¨ÃÂ© ÃÂ§ÃÂÃÂªÃÂ¶ÃÂ®ÃÂ: <b>{inflation_rate}%</b> ÃÂ³ÃÂÃÂÃÂÃÂ§ÃÂ\n"
            f"Ã°ÂÂÂ¸ ÃÂ®ÃÂ³ÃÂ§ÃÂ±ÃÂ© ÃÂ§ÃÂÃÂÃÂÃÂ© ÃÂ§ÃÂÃÂ´ÃÂ±ÃÂ§ÃÂ¦ÃÂÃÂ©: <b>{fmt(purchasing_loss)} {currency_name}</b>\n"
            f"Ã¢ÂÂ¨ ÃÂ§ÃÂÃÂ±ÃÂ¨ÃÂ­ ÃÂ§ÃÂÃÂ­ÃÂÃÂÃÂÃÂ: <b>{fmt(real_profit)} {currency_name}</b>\n\n"
        )
        result += _verdict(real_profit)

    # Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ ÃÂ°ÃÂÃÂ¨ Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
    elif tool == "tool_gold":
        gold = live.get("gold")
        if not gold:
            await bot.send_message(chat_id, "Ã¢ÂÂ ÃÂªÃÂ¹ÃÂ°ÃÂ± ÃÂ¬ÃÂÃÂ¨ ÃÂ£ÃÂ³ÃÂ¹ÃÂ§ÃÂ± ÃÂ§ÃÂÃÂ°ÃÂÃÂ¨ ÃÂ­ÃÂ§ÃÂÃÂÃÂ§ÃÂ. ÃÂ¬ÃÂ±ÃÂ¨ ÃÂªÃÂ§ÃÂÃÂ ÃÂ¨ÃÂ¹ÃÂ¯ ÃÂ´ÃÂÃÂÃÂ©.")
            return

        current_price = gold["current_gram_local"]
        forecast_map = {"dur_6m": gold["forecast_6m"], "dur_1y": gold["forecast_1y"], "dur_3y": gold["forecast_3y"]}
        expected_price = forecast_map[dur_key]

        grams = amount / current_price
        future_value = grams * expected_price
        profit = future_value - amount
        real_profit = profit - purchasing_loss

        result = (
            f"<b>Ã°ÂÂ¥Â ÃÂÃÂªÃÂÃÂ¬ÃÂ© ÃÂ§ÃÂÃÂ§ÃÂ³ÃÂªÃÂ«ÃÂÃÂ§ÃÂ± ÃÂÃÂ ÃÂ§ÃÂÃÂ°ÃÂÃÂ¨</b>\n"
            f"{PHARAOH_LINE}\n\n"
            f"{GOLD_DIAMOND} ÃÂ§ÃÂÃÂÃÂ¨ÃÂÃÂº: <b>{fmt(amount)} {currency_name}</b>\n"
            f"{GOLD_DIAMOND} ÃÂ§ÃÂÃÂÃÂ¯ÃÂ©: <b>{dur_text}</b>\n\n"
            f"Ã°ÂÂÂ <b>ÃÂ£ÃÂ³ÃÂ¹ÃÂ§ÃÂ± ÃÂÃÂ­ÃÂ¸ÃÂÃÂ©:</b>\n"
            f"   ÃÂ³ÃÂ¹ÃÂ± ÃÂ§ÃÂÃÂ¬ÃÂ±ÃÂ§ÃÂ ÃÂ§ÃÂÃÂ¢ÃÂ: <b>{fmt(current_price)} {currency_name}</b>\n"
            f"   (${fmt(gold['current_gram_usd'])} ÃÂ¹ÃÂ§ÃÂÃÂÃÂÃÂ§ÃÂ)\n\n"
            f"Ã°ÂÂÂ® <b>ÃÂ§ÃÂÃÂªÃÂÃÂÃÂ¹ÃÂ§ÃÂª</b> (ÃÂÃÂÃÂ {gold['growth_rate']}% ÃÂ³ÃÂÃÂÃÂÃÂ§ÃÂ):\n"
            f"   ÃÂ§ÃÂÃÂ³ÃÂ¹ÃÂ± ÃÂ§ÃÂÃÂÃÂªÃÂÃÂÃÂ¹ ÃÂ¨ÃÂ¹ÃÂ¯ {dur_text}: <b>{fmt(expected_price)} {currency_name}</b>\n\n"
            f"{'Ã¢ÂÂ' * 20}\n"
            f"Ã¢ÂÂÃ¯Â¸Â ÃÂÃÂªÃÂ´ÃÂªÃÂ±ÃÂ: <b>{fmt(grams)} ÃÂ¬ÃÂ±ÃÂ§ÃÂ</b>\n"
            f"Ã°ÂÂÂµ ÃÂ§ÃÂÃÂÃÂÃÂÃÂ© ÃÂ§ÃÂÃÂÃÂªÃÂÃÂÃÂ¹ÃÂ©: <b>{fmt(future_value)} {currency_name}</b>\n"
            f"Ã°ÂÂÂ ÃÂ§ÃÂÃÂ±ÃÂ¨ÃÂ­ ÃÂ§ÃÂÃÂÃÂªÃÂÃÂÃÂ¹: <b>{fmt(profit)} {currency_name}</b>\n\n"
            f"{'Ã¢ÂÂ' * 20}\n"
            f"Ã°ÂÂÂ <b>ÃÂªÃÂ£ÃÂ«ÃÂÃÂ± ÃÂ§ÃÂÃÂªÃÂ¶ÃÂ®ÃÂ</b> {inflation_source}\n"
            f"{'Ã¢ÂÂ' * 20}\n\n"
            f"Ã°ÂÂÂ» ÃÂ§ÃÂÃÂªÃÂ¶ÃÂ®ÃÂ: <b>{inflation_rate}%</b> ÃÂ³ÃÂÃÂÃÂÃÂ§ÃÂ\n"
            f"Ã°ÂÂÂ¸ ÃÂ®ÃÂ³ÃÂ§ÃÂ±ÃÂ© ÃÂ§ÃÂÃÂÃÂÃÂ© ÃÂ§ÃÂÃÂ´ÃÂ±ÃÂ§ÃÂ¦ÃÂÃÂ©: <b>{fmt(purchasing_loss)} {currency_name}</b>\n"
            f"Ã¢ÂÂ¨ ÃÂ§ÃÂÃÂ±ÃÂ¨ÃÂ­ ÃÂ§ÃÂÃÂ­ÃÂÃÂÃÂÃÂ: <b>{fmt(real_profit)} {currency_name}</b>\n\n"
        )
        result += _verdict(real_profit)

    # Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ ÃÂ¯ÃÂÃÂÃÂ§ÃÂ± Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
    elif tool == "tool_usd":
        hc = live.get("hard_currency")
        if not hc:
            await bot.send_message(chat_id, "Ã¢ÂÂ ÃÂªÃÂ¹ÃÂ°ÃÂ± ÃÂ¬ÃÂÃÂ¨ ÃÂ£ÃÂ³ÃÂ¹ÃÂ§ÃÂ± ÃÂ§ÃÂÃÂµÃÂ±ÃÂ ÃÂ­ÃÂ§ÃÂÃÂÃÂ§ÃÂ. ÃÂ¬ÃÂ±ÃÂ¨ ÃÂªÃÂ§ÃÂÃÂ.")
            return

        current_rate = hc["current_rate"]
        forecast_map = {"dur_6m": hc["forecast_6m"], "dur_1y": hc["forecast_1y"], "dur_3y": hc["forecast_3y"]}
        expected_rate = forecast_map[dur_key]

        dollars = amount / current_rate
        future_value = dollars * expected_rate
        profit = future_value - amount
        real_profit = profit - purchasing_loss

        result = (
            f"<b>Ã°ÂÂÂµ ÃÂÃÂªÃÂÃÂ¬ÃÂ© ÃÂ§ÃÂÃÂ§ÃÂ³ÃÂªÃÂ«ÃÂÃÂ§ÃÂ± ÃÂÃÂ ÃÂ§ÃÂÃÂ¯ÃÂÃÂÃÂ§ÃÂ±</b>\n"
            f"{PHARAOH_LINE}\n\n"
            f"{GOLD_DIAMOND} ÃÂ§ÃÂÃÂÃÂ¨ÃÂÃÂº: <b>{fmt(amount)} {currency_name}</b>\n"
            f"{GOLD_DIAMOND} ÃÂ§ÃÂÃÂÃÂ¯ÃÂ©: <b>{dur_text}</b>\n\n"
            f"Ã°ÂÂÂ <b>ÃÂ³ÃÂ¹ÃÂ± ÃÂÃÂ­ÃÂ¸ÃÂ:</b>\n"
            f"   ÃÂ§ÃÂÃÂ¯ÃÂÃÂÃÂ§ÃÂ± ÃÂ§ÃÂÃÂ¢ÃÂ: <b>{fmt(current_rate)} {currency_name}</b>\n\n"
            f"Ã°ÂÂÂ® <b>ÃÂ§ÃÂÃÂªÃÂÃÂÃÂ¹ÃÂ§ÃÂª</b> (ÃÂªÃÂºÃÂÃÂ± {hc['change_rate']}% ÃÂ³ÃÂÃÂÃÂÃÂ§ÃÂ):\n"
            f"   ÃÂ§ÃÂÃÂ³ÃÂ¹ÃÂ± ÃÂ§ÃÂÃÂÃÂªÃÂÃÂÃÂ¹ ÃÂ¨ÃÂ¹ÃÂ¯ {dur_text}: <b>{fmt(expected_rate)} {currency_name}</b>\n\n"
            f"{'Ã¢ÂÂ' * 20}\n"
            f"Ã°ÂÂÂ² ÃÂÃÂªÃÂ´ÃÂªÃÂ±ÃÂ: <b>{fmt(dollars)} ÃÂ¯ÃÂÃÂÃÂ§ÃÂ±</b>\n"
            f"Ã°ÂÂÂµ ÃÂ§ÃÂÃÂÃÂÃÂÃÂ© ÃÂ§ÃÂÃÂÃÂªÃÂÃÂÃÂ¹ÃÂ©: <b>{fmt(future_value)} {currency_name}</b>\n"
            f"Ã°ÂÂÂ ÃÂ§ÃÂÃÂ±ÃÂ¨ÃÂ­ ÃÂ§ÃÂÃÂÃÂªÃÂÃÂÃÂ¹: <b>{fmt(profit)} {currency_name}</b>\n\n"
            f"{'Ã¢ÂÂ' * 20}\n"
            f"Ã°ÂÂÂ <b>ÃÂªÃÂ£ÃÂ«ÃÂÃÂ± ÃÂ§ÃÂÃÂªÃÂ¶ÃÂ®ÃÂ</b> {inflation_source}\n"
            f"{'Ã¢ÂÂ' * 20}\n\n"
            f"Ã°ÂÂÂ» ÃÂ§ÃÂÃÂªÃÂ¶ÃÂ®ÃÂ: <b>{inflation_rate}%</b> ÃÂ³ÃÂÃÂÃÂÃÂ§ÃÂ\n"
            f"Ã°ÂÂÂ¸ ÃÂ®ÃÂ³ÃÂ§ÃÂ±ÃÂ© ÃÂ§ÃÂÃÂÃÂÃÂ© ÃÂ§ÃÂÃÂ´ÃÂ±ÃÂ§ÃÂ¦ÃÂÃÂ©: <b>{fmt(purchasing_loss)} {currency_name}</b>\n"
            f"Ã¢ÂÂ¨ ÃÂ§ÃÂÃÂ±ÃÂ¨ÃÂ­ ÃÂ§ÃÂÃÂ­ÃÂÃÂÃÂÃÂ: <b>{fmt(real_profit)} {currency_name}</b>\n\n"
        )
        result += _verdict(real_profit)

    result += f"\n<i>Ã°ÂÂÂ¢ ÃÂ§ÃÂÃÂÃÂªÃÂ§ÃÂ¦ÃÂ¬ ÃÂªÃÂÃÂ¯ÃÂÃÂ±ÃÂÃÂ© ÃÂÃÂÃÂÃÂ³ÃÂª ÃÂÃÂµÃÂÃÂ­ÃÂ© ÃÂÃÂ§ÃÂÃÂÃÂ©</i>"

    btns = await result_buttons()
    await send_logo(chat_id, result, reply_markup=btns)
    await state.clear()


def _verdict(real_profit: float) -> str:
    if real_profit > 0:
        return f"Ã¢ÂÂ <b>ÃÂ§ÃÂ³ÃÂªÃÂ«ÃÂÃÂ§ÃÂ±ÃÂ ÃÂÃÂªÃÂºÃÂÃÂ¨ ÃÂ¹ÃÂÃÂ ÃÂ§ÃÂÃÂªÃÂ¶ÃÂ®ÃÂ!</b> Ã°ÂÂÂ"
    else:
        return f"Ã¢ÂÂ Ã¯Â¸Â <b>ÃÂ§ÃÂ³ÃÂªÃÂ«ÃÂÃÂ§ÃÂ±ÃÂ ÃÂÃÂ§ ÃÂÃÂªÃÂºÃÂÃÂ¨ ÃÂ¹ÃÂÃÂ ÃÂ§ÃÂÃÂªÃÂ¶ÃÂ®ÃÂ</b>"


# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
#           ÃÂÃÂÃÂ­ÃÂ© ÃÂªÃÂ­ÃÂÃÂ ÃÂ§ÃÂÃÂ£ÃÂ¯ÃÂÃÂ
# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ

@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()

    users = await get_users_count()
    settings = await get_all_settings()
    by_country = await get_users_by_country()

    country_stats = "\n".join(
        [f"   {c or 'ÃÂºÃÂÃÂ± ÃÂÃÂ­ÃÂ¯ÃÂ¯'}: {n}" for c, n in by_country[:10]]
    ) if by_country else "   ÃÂÃÂ§ ÃÂÃÂÃÂ¬ÃÂ¯"

    text = (
        f"<b>Ã¢ÂÂÃ¯Â¸Â ÃÂÃÂÃÂ­ÃÂ© ÃÂªÃÂ­ÃÂÃÂ ÃÂ§ÃÂÃÂ£ÃÂ¯ÃÂÃÂ</b>\n"
        f"{PHARAOH_LINE}\n\n"
        f"Ã°ÂÂÂ¥ ÃÂ§ÃÂÃÂÃÂ³ÃÂªÃÂ®ÃÂ¯ÃÂÃÂÃÂ: <b>{users}</b>\n"
        f"Ã°ÂÂÂ ÃÂ­ÃÂ³ÃÂ¨ ÃÂ§ÃÂÃÂ¯ÃÂÃÂÃÂ©:\n{country_stats}\n\n"
        f"<b>Ã°ÂÂÂ ÃÂ§ÃÂÃÂ¥ÃÂ¹ÃÂ¯ÃÂ§ÃÂ¯ÃÂ§ÃÂª:</b>\n"
        f"Ã°ÂÂ¥Â ÃÂÃÂÃÂ ÃÂ§ÃÂÃÂ°ÃÂÃÂ¨ ÃÂ§ÃÂÃÂ³ÃÂÃÂÃÂ: <b>{settings.get('gold_annual_growth', 10)}%</b>\n"
        f"Ã°ÂÂÂµ ÃÂªÃÂºÃÂÃÂ± ÃÂ§ÃÂÃÂ¹ÃÂÃÂÃÂ© ÃÂ§ÃÂÃÂ³ÃÂÃÂÃÂ: <b>{settings.get('currency_annual_change', 8)}%</b>\n"
        f"Ã°ÂÂÂ ÃÂªÃÂ¶ÃÂ®ÃÂ ÃÂ§ÃÂÃÂªÃÂ±ÃÂ§ÃÂ¶ÃÂ: <b>{settings.get('fallback_inflation', 15)}%</b>\n"
        f"Ã°ÂÂÂ ÃÂ±ÃÂ§ÃÂ¨ÃÂ·: <a href=\"{settings.get('result_link_url', '#')}\">"
        f"{settings.get('result_link_text', 'ÃÂ§ÃÂÃÂÃÂÃÂÃÂ¹')}</a>\n"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Ã°ÂÂ¥Â ÃÂÃÂÃÂ ÃÂ§ÃÂÃÂ°ÃÂÃÂ¨ ÃÂ§ÃÂÃÂ³ÃÂÃÂÃÂ %", callback_data="edit_gold_annual_growth")],
        [InlineKeyboardButton(text="Ã°ÂÂÂµ ÃÂªÃÂºÃÂÃÂ± ÃÂ§ÃÂÃÂ¹ÃÂÃÂÃÂ© ÃÂ§ÃÂÃÂ³ÃÂÃÂÃÂ %", callback_data="edit_currency_annual_change")],
        [InlineKeyboardButton(text="Ã°ÂÂÂ ÃÂªÃÂ¶ÃÂ®ÃÂ ÃÂ§ÃÂÃÂªÃÂ±ÃÂ§ÃÂ¶ÃÂ %", callback_data="edit_fallback_inflation")],
        [InlineKeyboardButton(text="Ã°ÂÂÂ ÃÂªÃÂ¹ÃÂ¯ÃÂÃÂ ÃÂ§ÃÂÃÂ±ÃÂ§ÃÂ¨ÃÂ·", callback_data="edit_result_link")],
        [InlineKeyboardButton(
            text="Ã°ÂÂÂ¢ ÃÂ±ÃÂ³ÃÂ§ÃÂÃÂ© ÃÂ¬ÃÂÃÂ§ÃÂ¹ÃÂÃÂ©",
            callback_data="admin_broadcast"
        )],
    ])

    await message.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML,
                         disable_web_page_preview=True)


@router.message(Command("myid"))
async def cmd_myid(message: Message):
    await message.answer(f"Ã°ÂÂÂ ÃÂÃÂ¹ÃÂ±ÃÂÃÂ: <code>{message.from_user.id}</code>",
                         parse_mode=ParseMode.HTML)


SETTING_LABELS = {
    "gold_annual_growth": "ÃÂÃÂ³ÃÂ¨ÃÂ© ÃÂÃÂÃÂ ÃÂ§ÃÂÃÂ°ÃÂÃÂ¨ ÃÂ§ÃÂÃÂ³ÃÂÃÂÃÂÃÂ© %",
    "currency_annual_change": "ÃÂÃÂ³ÃÂ¨ÃÂ© ÃÂªÃÂºÃÂÃÂ± ÃÂ§ÃÂÃÂ¹ÃÂÃÂÃÂ© ÃÂ§ÃÂÃÂ³ÃÂÃÂÃÂÃÂ© %",
    "fallback_inflation": "ÃÂÃÂ³ÃÂ¨ÃÂ© ÃÂ§ÃÂÃÂªÃÂ¶ÃÂ®ÃÂ ÃÂ§ÃÂÃÂ§ÃÂÃÂªÃÂ±ÃÂ§ÃÂ¶ÃÂÃÂ© %",
}


@router.callback_query(F.data.startswith("edit_"))
async def edit_setting(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return

    key = callback.data.replace("edit_", "")

    if key == "result_link":
        await state.set_state(AdminStates.waiting_link_text)
        await callback.message.answer(
            "Ã°ÂÂÂ <b>ÃÂªÃÂ¹ÃÂ¯ÃÂÃÂ ÃÂ§ÃÂÃÂ±ÃÂ§ÃÂ¨ÃÂ·</b>\n\nÃÂ§ÃÂÃÂªÃÂ¨ ÃÂÃÂµ ÃÂ§ÃÂÃÂ²ÃÂ± ÃÂ§ÃÂÃÂ¬ÃÂ¯ÃÂÃÂ¯:",
            parse_mode=ParseMode.HTML
        )
        return

    if key not in SETTING_LABELS:
        return

    current = await get_setting(key)
    await state.update_data(editing_key=key)
    await state.set_state(AdminStates.waiting_setting_value)
    await callback.message.answer(
        f"Ã¢ÂÂÃ¯Â¸Â <b>{SETTING_LABELS[key]}</b>\n\n"
        f"ÃÂ§ÃÂÃÂÃÂÃÂÃÂ© ÃÂ§ÃÂÃÂ­ÃÂ§ÃÂÃÂÃÂ©: <b>{current}</b>\n\nÃÂ§ÃÂÃÂªÃÂ¨ ÃÂ§ÃÂÃÂÃÂÃÂÃÂ© ÃÂ§ÃÂÃÂ¬ÃÂ¯ÃÂÃÂ¯ÃÂ©:",
        parse_mode=ParseMode.HTML
    )


@router.message(AdminStates.waiting_setting_value)
async def save_setting_value(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        value = float(message.text.strip())
    except ValueError:
        await message.answer("Ã¢ÂÂ ÃÂ£ÃÂ¯ÃÂ®ÃÂ ÃÂ±ÃÂÃÂ ÃÂµÃÂ­ÃÂÃÂ­!")
        return

    data = await state.get_data()
    key = data["editing_key"]
    await set_setting(key, value)

    # ÃÂªÃÂ­ÃÂ¯ÃÂÃÂ« config ÃÂ§ÃÂÃÂÃÂ¨ÃÂ§ÃÂ´ÃÂ± ÃÂÃÂ ÃÂÃÂ­ÃÂªÃÂ§ÃÂ¬
    import config
    if key == "gold_annual_growth":
        config.DEFAULT_GOLD_ANNUAL_GROWTH = value
    elif key == "currency_annual_change":
        config.DEFAULT_CURRENCY_ANNUAL_CHANGE = value

    await state.clear()
    await message.answer(
        f"Ã¢ÂÂ ÃÂªÃÂ ÃÂªÃÂ¹ÃÂ¯ÃÂÃÂ <b>{SETTING_LABELS[key]}</b> ÃÂ¥ÃÂÃÂ: <b>{value}</b>\n\n/admin",
        parse_mode=ParseMode.HTML
    )


@router.message(AdminStates.waiting_link_text)
async def edit_link_text(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await set_setting("result_link_text", message.text.strip())
    await state.set_state(AdminStates.waiting_link_url)
    await message.answer("Ã¢ÂÂ ÃÂ§ÃÂÃÂ¢ÃÂ ÃÂ§ÃÂÃÂªÃÂ¨ ÃÂ§ÃÂÃÂ±ÃÂ§ÃÂ¨ÃÂ· (URL):")


@router.message(AdminStates.waiting_link_url)
async def edit_link_url(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    url = message.text.strip()
    if not (url.startswith("http://") or url.startswith("https://") or url.startswith("tg://")):
        await message.answer("Ã¢ÂÂ ÃÂ§ÃÂÃÂ±ÃÂ§ÃÂ¨ÃÂ· ÃÂÃÂ§ÃÂ²ÃÂ ÃÂÃÂ¨ÃÂ¯ÃÂ£ ÃÂ¨ÃÂ http:// ÃÂ£ÃÂ https://")
        return
    await set_setting("result_link_url", url)
    await state.clear()
    await message.answer("Ã¢ÂÂ ÃÂªÃÂ ÃÂªÃÂ­ÃÂ¯ÃÂÃÂ« ÃÂ§ÃÂÃÂ±ÃÂ§ÃÂ¨ÃÂ·!\n\n/admin")


# Ã¢ÂÂÃ¢ÂÂ Broadcast Ã¢ÂÂÃ¢ÂÂ

@router.callback_query(F.data == "admin_broadcast")
async def broadcast_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.waiting_broadcast_message)
    await callback.message.answer(
        "Ã°ÂÂÂ¢ <b>ÃÂ±ÃÂ³ÃÂ§ÃÂÃÂ© ÃÂ¬ÃÂÃÂ§ÃÂ¹ÃÂÃÂ©</b>\n\n"
        "ÃÂ§ÃÂÃÂªÃÂ¨ ÃÂ§ÃÂÃÂ±ÃÂ³ÃÂ§ÃÂÃÂ© (ÃÂÃÂ¯ÃÂ¹ÃÂ HTML)\n/cancel ÃÂÃÂÃÂ¥ÃÂÃÂºÃÂ§ÃÂ¡",
        parse_mode=ParseMode.HTML
    )


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Ã¢ÂÂ ÃÂªÃÂ ÃÂ§ÃÂÃÂ¥ÃÂÃÂºÃÂ§ÃÂ¡")


@router.message(AdminStates.waiting_broadcast_message)
async def broadcast_send(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    user_ids = await get_all_user_ids()
    total = len(user_ids)
    success = failed = 0

    status = await message.answer(f"Ã°ÂÂÂ¤ ÃÂ¬ÃÂ§ÃÂ±ÃÂ ÃÂ§ÃÂÃÂ¥ÃÂ±ÃÂ³ÃÂ§ÃÂ ÃÂÃÂ {total}...")

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
        f"Ã¢ÂÂ <b>ÃÂªÃÂ ÃÂ§ÃÂÃÂ¥ÃÂ±ÃÂ³ÃÂ§ÃÂ</b>\n\nÃ°ÂÂÂ ÃÂ§ÃÂÃÂ¥ÃÂ¬ÃÂÃÂ§ÃÂÃÂ: {total}\nÃ¢ÂÂ ÃÂÃÂ¬ÃÂ§ÃÂ­: {success}\nÃ¢ÂÂ ÃÂÃÂ´ÃÂ: {failed}",
        parse_mode=ParseMode.HTML
    )


# Ã¢ÂÂÃ¢ÂÂ Fallback Ã¢ÂÂÃ¢ÂÂ

@router.message()
async def fallback(message: Message, state: FSMContext):
    current = await state.get_state()
    if current and "Admin" in current:
        return
    if current is None:
        is_sub = await check_subscription(message.from_user.id)
        if not is_sub:
            await message.answer("Ã¢ÂÂ Ã¯Â¸Â ÃÂ§ÃÂ´ÃÂªÃÂ±ÃÂ ÃÂÃÂ ÃÂ§ÃÂÃÂÃÂÃÂ§ÃÂ©!", reply_markup=sub_kb())
        else:
            await message.answer(f"ÃÂ§ÃÂÃÂªÃÂ¨ /start ÃÂ¹ÃÂ´ÃÂ§ÃÂ ÃÂªÃÂ¨ÃÂ¯ÃÂ£ {ANKH}")


# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
#              ÃÂ§ÃÂÃÂªÃÂ´ÃÂºÃÂÃÂ
# Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ

async def on_startup(b: Bot = None):
    b = b or bot
    await init_db()
    if USE_WEBHOOK:
        await b.set_webhook(WEBHOOK_URL)
        logger.info(f"Webhook: {WEBHOOK_URL}")


async def on_shutdown(b: Bot = None):
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
