"""
بوت اقتصاد أحمس v2 - حاسبة التضخم والاستثمار
=================================================
بيانات لحظية | كل دول العالم | ألوان مستوحاة من اللوجو
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


# ══════════════════════════════════════
#              حالات FSM
# ══════════════════════════════════════

class InvestForm(StatesGroup):
    waiting_country = State()
    waiting_amount = State()
    waiting_duration = State()
    waiting_tool = State()
    waiting_bank_rate = State()  # المستخدم يدخل نسبة الشهادة


class AdminStates(StatesGroup):
    waiting_setting_value = State()
    waiting_broadcast_message = State()
    waiting_link_text = State()
    waiting_link_url = State()


# ══════════════════════════════════════
#              أدوات مساعدة
# ══════════════════════════════════════

# ── ألوان مستوحاة من اللوجو (للاستخدام في الرسائل) ──
# ذهبي ☀️ | أسود 🖤 | أزرق سيان 🔷 | رمادي ⚙️
# نستخدم إيموجي ذهبية + خطوط فرعونية

PHARAOH_LINE = "═══════════════════"
GOLD_DIAMOND = "◈"
ANKH = "☥"

def fmt(n: float) -> str:
    if n == int(n):
        return f"{int(n):,}"
    return f"{n:,.2f}"


async def check_subscription(user_id: int) -> bool:
    # TODO: re-enable after testing by uncommenting below
    return True
    # try:
    #     member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
    #     return member.status in [
    #         ChatMemberStatus.MEMBER,
    #         ChatMemberStatus.ADMINISTRATOR,
    #         ChatMemberStatus.CREATOR
    #     ]
    # except Exception as e:
    #     logger.error(f"Sub check error: {e}")
    #     return False


def sub_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 اشترك في القناة", url=CHANNEL_LINK)],
        [InlineKeyboardButton(text=f"{ANKH} تحققت من الاشتراك", callback_data="check_sub")]
    ])


async def send_logo(chat_id: int, caption: str, reply_markup=None):
    """إرسال اللوجو مع رسالة"""
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
        [InlineKeyboardButton(text=f"🌐 {link_text}", url=link_url)],
        [InlineKeyboardButton(text=f"{ANKH} حساب جديد", callback_data="new_calc")]
    ])


def is_admin(uid: int) -> bool:
    return uid in ADMIN_IDS


def country_keyboard(page: int = 0) -> InlineKeyboardMarkup:
    """أزرار اختيار الدولة مع سكرول"""
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

    # أزرار التنقل
    nav = []
    if has_prev:
        nav.append(InlineKeyboardButton(text="◀️ السابق", callback_data=f"cpage_{page-1}"))
    nav.append(InlineKeyboardButton(text=f"📄 {page+1}", callback_data="noop"))
    if has_next:
        nav.append(InlineKeyboardButton(text="التالي ▶️", callback_data=f"cpage_{page+1}"))
    rows.append(nav)

    return InlineKeyboardMarkup(inline_keyboard=rows)


def search_results_keyboard(results: list) -> InlineKeyboardMarkup:
    """أزرار نتائج البحث"""
    rows = []
    for c in results:
        rows.append([InlineKeyboardButton(
            text=f"{c['flag']} {c['name_ar']} ({c['currency']})",
            callback_data=f"country_{c['code']}"
        )])
    rows.append([InlineKeyboardButton(text="📋 عرض كل الدول", callback_data="cpage_0")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def duration_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="6️⃣ شهور", callback_data="dur_6m"),
        InlineKeyboardButton(text="1️⃣ سنة", callback_data="dur_1y"),
        InlineKeyboardButton(text="3️⃣ سنوات", callback_data="dur_3y"),
    ]])


def tool_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏦 شهادات بنكية", callback_data="tool_bank")],
        [InlineKeyboardButton(text=f"🥇 ذهب عيار 24 (سعر لحظي)", callback_data="tool_gold")],
        [InlineKeyboardButton(text="💵 عملة صعبة (دولار)", callback_data="tool_usd")],
    ])


# ══════════════════════════════════════
#           أوامر المستخدم
# ══════════════════════════════════════

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
            f"<b>{GOLD_DIAMOND} حاسب على فلوسك {GOLD_DIAMOND}</b>\n"
            f"{PHARAOH_LINE}\n\n"
            "التضخم مش بيستنى حد\n"
            "اعرف دلوقتي: استثمارك بيكسب\n"
            "ولا بيخسر من غير ما تحس؟ ⚡\n\n"
            "⚠️ لازم تكون مشترك في القناة الأول\n\n"
            "📢 اشترك وبعدين اضغط تحقق 👇",
            reply_markup=sub_kb()
        )
        return

    await ask_country(message.chat.id, state)


async def ask_country(chat_id: int, state: FSMContext):
    """سؤال المستخدم عن بلده"""
    await state.set_state(InvestForm.waiting_country)

    # أشهر 4 دول كاختصار سريع + زر عرض الكل
    quick_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇪🇬 مصر", callback_data="country_EG"),
            InlineKeyboardButton(text="🇸🇦 السعودية", callback_data="country_SA"),
        ],
        [
            InlineKeyboardButton(text="🇦🇪 الإمارات", callback_data="country_AE"),
            InlineKeyboardButton(text="🇹🇷 تركيا", callback_data="country_TR"),
        ],
        [InlineKeyboardButton(text="📋 عرض كل الدول", callback_data="cpage_0")],
    ])

    await bot.send_message(
        chat_id,
        f"<b>{GOLD_DIAMOND} حاسبة التضخم والاستثمار {GOLD_DIAMOND}</b>\n"
        f"{PHARAOH_LINE}\n\n"
        "🌍 <b>اكتب اسم بلدك</b> عشان نجيبلك الأسعار اللحظية\n"
        "<i>(مثال: مصر، تركيا، Egypt...)</i>\n\n"
        "أو اختار من الأكثر شيوعاً 👇",
        reply_markup=quick_kb,
        parse_mode=ParseMode.HTML
    )


@router.callback_query(F.data == "check_sub")
async def check_sub_cb(callback: CallbackQuery, state: FSMContext):
    is_sub = await check_subscription(callback.from_user.id)
    if is_sub:
        await callback.message.delete()
        await ask_country(callback.message.chat.id, state)
    else:
        await callback.answer("❌ لسه مشترك! اشترك الأول", show_alert=True)


@router.callback_query(F.data == "new_calc")
async def new_calc_cb(callback: CallbackQuery, state: FSMContext):
    is_sub = await check_subscription(callback.from_user.id)
    if not is_sub:
        await callback.message.answer("⚠️ اشترك في القناة الأول!", reply_markup=sub_kb())
        return
    await ask_country(callback.message.chat.id, state)


# ── تصفح الدول ──

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


# ── البحث عن الدولة بالكتابة ──
@router.message(InvestForm.waiting_country)
async def search_country_text(message: Message, state: FSMContext):
    """المستخدم كتب اسم بلده بدل ما يضغط زر"""
    query = message.text.strip()
    results = search_countries(query, limit=6)

    if not results:
        await message.answer(
            f"❌ مفيش دولة اسمها <b>{query}</b>\n\n"
            "جرب تكتب اسم تاني أو اختار من القائمة 👇",
            parse_mode=ParseMode.HTML,
            reply_markup=country_keyboard(0)
        )
        return

    if len(results) == 1:
        # نتيجة واحدة → اختارها مباشرة
        country = results[0]
        await _select_country(message.chat.id, message.from_user, country, state)
        return

    # أكثر من نتيجة → عرضها كأزرار
    await message.answer(
        f"🔍 نتائج البحث عن <b>{query}</b>:",
        parse_mode=ParseMode.HTML,
        reply_markup=search_results_keyboard(results)
    )


# ── اختيار الدولة ──

@router.callback_query(F.data.startswith("country_"), InvestForm.waiting_country)
async def select_country_cb(callback: CallbackQuery, state: FSMContext):
    code = callback.data.replace("country_", "")
    country = get_country_by_code(code)
    if not country:
        await callback.answer("❌ خطأ", show_alert=True)
        return
    try:
        await callback.message.delete()
    except Exception:
        pass
    await _select_country(callback.message.chat.id, callback.from_user, country, state)


async def _select_country(chat_id: int, user, country: dict, state: FSMContext):
    """معالجة اختيار الدولة (مشتركة بين الضغط والكتابة)"""
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
        f"⏳ جاري جلب البيانات اللحظية لـ {country['flag']} {country['name_ar']}..."
    )

    live_data = await fetch_all_data(country["code"], country["currency"])
    await state.update_data(country=country, live_data=live_data)

    summary = f"<b>{GOLD_DIAMOND} {country['flag']} أسعار {country['name_ar']} اللحظية {GOLD_DIAMOND}</b>\n"
    summary += f"{PHARAOH_LINE}\n\n"

    if live_data["gold"]:
        g = live_data["gold"]
        fb_tag = " <i>(تقديري)</i>" if g.get("is_fallback") else ""
        summary += f"🥇 <b>الذهب (عيار 24):</b> {fmt(g['current_gram_local'])} {country['currency_name']}/جرام{fb_tag}\n"
        summary += f"   <i>(${fmt(g['current_gram_usd'])} عالمياً)</i>\n\n"

    if live_data["hard_currency"]:
        h = live_data["hard_currency"]
        summary += f"💵 <b>الدولار:</b> {fmt(h['current_rate'])} {country['currency_name']}\n\n"

    if live_data["inflation"]:
        inf_data = live_data["inflation"]
        summary += f"📉 <b>التضخم:</b> {inf_data['rate']}% <i>(آخر بيانات: {inf_data['year']} - {inf_data['source']})</i>\n\n"
    else:
        fb = await get_setting("fallback_inflation")
        summary += f"📉 <b>التضخم:</b> {fb}% <i>(تقديري)</i>\n\n"

    summary += f"{PHARAOH_LINE}\n"
    summary += "💰 <b>اكتب المبلغ اللي عايز تستثمره</b>\n"
    summary += f"<i>(أرقام فقط بـ {country['currency_name']})</i>"

    await state.set_state(InvestForm.waiting_amount)
    try:
        await loading.delete()
    except Exception:
        pass
    await bot.send_message(chat_id, summary, parse_mode=ParseMode.HTML)


# ── إدخال المبلغ ──

@router.message(InvestForm.waiting_amount)
async def receive_amount(message: Message, state: FSMContext):
    text = message.text.strip().replace(",", "").replace("٬", "").replace("،", "")
    try:
        amount = float(text)
        if amount <= 0:
            raise ValueError
        if amount > 999_999_999_999:
            await message.answer("⚠️ المبلغ كبير أوي!")
            return
    except (ValueError, TypeError):
        await message.answer(
            "❌ <b>إدخال غير صحيح</b>\n\nاكتب أرقام فقط\nمثال: <code>100000</code>",
            parse_mode=ParseMode.HTML
        )
        return

    data = await state.get_data()
    country = data["country"]
    await state.update_data(amount=amount)
    await state.set_state(InvestForm.waiting_duration)
    await message.answer(
        f"💰 المبلغ: <b>{fmt(amount)} {country['currency_name']}</b>\n\n"
        "⏳ اختار مدة الاستثمار 👇",
        reply_markup=duration_kb(),
        parse_mode=ParseMode.HTML
    )


# ── اختيار المدة ──

@router.callback_query(F.data.startswith("dur_"), InvestForm.waiting_duration)
async def receive_duration(callback: CallbackQuery, state: FSMContext):
    dur_map = {"dur_6m": ("6 شهور", 0.5), "dur_1y": ("سنة", 1.0), "dur_3y": ("3 سنوات", 3.0)}
    dur_text, dur_years = dur_map[callback.data]

    await state.update_data(duration_text=dur_text, duration_years=dur_years, dur_key=callback.data)
    await state.set_state(InvestForm.waiting_tool)

    data = await state.get_data()
    country = data["country"]
    await callback.message.edit_text(
        f"💰 المبلغ: <b>{fmt(data['amount'])} {country['currency_name']}</b>\n"
        f"⏳ المدة: <b>{dur_text}</b>\n\n"
        "📊 اختار أداة الاستثمار 👇",
        reply_markup=tool_kb(),
        parse_mode=ParseMode.HTML
    )


# ── اختيار الأداة ──

@router.callback_query(F.data.startswith("tool_"), InvestForm.waiting_tool)
async def receive_tool(callback: CallbackQuery, state: FSMContext):
    tool = callback.data

    if tool == "tool_bank":
        # الشهادة: المستخدم يدخل نسبة الفائدة بنفسه
        await state.update_data(tool=tool)
        await state.set_state(InvestForm.waiting_bank_rate)
        await callback.message.edit_text(
            "🏦 <b>شهادات بنكية</b>\n"
            f"{PHARAOH_LINE}\n\n"
            "📝 <b>اكتب نسبة الفائدة السنوية لشهادتك</b>\n"
            "<i>(رقم فقط - مثال: 27)</i>\n\n"
            "💡 النسبة بتختلف حسب البنك ونوع الشهادة",
            parse_mode=ParseMode.HTML
        )
        return

    # الذهب والدولار: حساب مباشر
    await state.update_data(tool=tool)
    await calculate_result(callback, state)


# ── إدخال نسبة الشهادة البنكية ──

@router.message(InvestForm.waiting_bank_rate)
async def receive_bank_rate(message: Message, state: FSMContext):
    try:
        rate = float(message.text.strip().replace("%", ""))
        if rate <= 0 or rate > 100:
            raise ValueError
    except (ValueError, TypeError):
        await message.answer("❌ اكتب نسبة صحيحة (مثال: 27)")
        return

    await state.update_data(bank_rate=rate)

    # نحاكي callback عشان نستخدم نفس الدالة
    data = await state.get_data()
    await calculate_and_send(message.chat.id, data, state)


# ══════════════════════════════════════
#           حساب النتيجة
# ══════════════════════════════════════

async def calculate_result(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await callback.message.edit_text("⏳ جاري الحساب...")
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

    # ── التضخم ──
    if live["inflation"]:
        inflation_rate = live["inflation"]["rate"]
        inflation_source = f"({live['inflation']['source']} - {live['inflation']['year']})"
    else:
        inflation_rate = await get_setting("fallback_inflation")
        inflation_source = "(تقديري)"

    inf = inflation_rate / 100
    purchasing_loss = amount * (1 - (1 / ((1 + inf) ** dur_years)))

    result = ""

    # ════════ شهادات بنكية ════════
    if tool == "tool_bank":
        rate = data["bank_rate"] / 100
        total_return = amount * rate * dur_years
        final = amount + total_return
        real_profit = total_return - purchasing_loss

        result = (
            f"<b>🏦 نتيجة الاستثمار في شهادات بنكية</b>\n"
            f"{PHARAOH_LINE}\n\n"
            f"{GOLD_DIAMOND} المبلغ: <b>{fmt(amount)} {currency_name}</b>\n"
            f"{GOLD_DIAMOND} المدة: <b>{dur_text}</b>\n"
            f"{GOLD_DIAMOND} نسبة الفائدة: <b>{data['bank_rate']}%</b> سنوياً\n\n"
            f"💵 العائد الإجمالي: <b>{fmt(total_return)} {currency_name}</b>\n"
            f"🏷️ المبلغ النهائي: <b>{fmt(final)} {currency_name}</b>\n\n"
            f"{'─' * 20}\n"
            f"📉 <b>تأثير التضخم</b> {inflation_source}\n"
            f"{'─' * 20}\n\n"
            f"🔻 نسبة التضخم: <b>{inflation_rate}%</b> سنوياً\n"
            f"💸 خسارة القوة الشرائية: <b>{fmt(purchasing_loss)} {currency_name}</b>\n"
            f"✨ الربح الحقيقي: <b>{fmt(real_profit)} {currency_name}</b>\n\n"
        )
        result += _verdict(real_profit)

    # ════════ ذهب ════════
    elif tool == "tool_gold":
        gold = live.get("gold")
        if not gold:
            error_kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 جرب تاني", callback_data="new_calc")],
                [InlineKeyboardButton(text="🏦 جرب شهادات بنكية", callback_data="tool_bank")],
                [InlineKeyboardButton(text="💵 جرب دولار", callback_data="tool_usd")],
            ])
            await bot.send_message(
                chat_id,
                "❌ تعذر جلب أسعار الذهب حالياً\n\n"
                "ممكن تجرب أداة تانية أو تبدأ من جديد 👇",
                reply_markup=error_kb
            )
            await state.clear()
            return

        current_price = gold["current_gram_local"]
        forecast_map = {"dur_6m": gold["forecast_6m"], "dur_1y": gold["forecast_1y"], "dur_3y": gold["forecast_3y"]}
        expected_price = forecast_map[dur_key]

        grams = amount / current_price
        future_value = grams * expected_price
        profit = future_value - amount
        real_profit = profit - purchasing_loss

        result = (
            f"<b>🥇 نتيجة الاستثمار في الذهب (عيار 24)</b>\n"
            f"{PHARAOH_LINE}\n\n"
            f"{GOLD_DIAMOND} المبلغ: <b>{fmt(amount)} {currency_name}</b>\n"
            f"{GOLD_DIAMOND} المدة: <b>{dur_text}</b>\n\n"
            f"📊 <b>أسعار {'تقديرية' if gold.get('is_fallback') else 'لحظية'}:</b>\n"
            f"   سعر جرام عيار 24: <b>{fmt(current_price)} {currency_name}</b>\n"
            f"   (${fmt(gold['current_gram_usd'])} عالمياً){' ⚠️ تقديري' if gold.get('is_fallback') else ''}\n\n"
            f"🔮 <b>التوقعات</b> (نمو {gold['growth_rate']}% سنوياً - متوسط آخر 20 سنة):\n"
            f"   السعر المتوقع بعد {dur_text}: <b>{fmt(expected_price)} {currency_name}</b>\n\n"
            f"{'─' * 20}\n"
            f"⚖️ هتشتري: <b>{fmt(grams)} جرام</b>\n"
            f"💵 القيمة المتوقعة: <b>{fmt(future_value)} {currency_name}</b>\n"
            f"📈 الربح المتوقع: <b>{fmt(profit)} {currency_name}</b>\n\n"
            f"{'─' * 20}\n"
            f"📉 <b>تأثير التضخم</b> {inflation_source}\n"
            f"{'─' * 20}\n\n"
            f"🔻 التضخم: <b>{inflation_rate}%</b> سنوياً\n"
            f"💸 خسارة القوة الشرائية: <b>{fmt(purchasing_loss)} {currency_name}</b>\n"
            f"✨ الربح الحقيقي: <b>{fmt(real_profit)} {currency_name}</b>\n\n"
        )
        result += _verdict(real_profit)

    # ════════ دولار ════════
    elif tool == "tool_usd":
        hc = live.get("hard_currency")
        if not hc:
            error_kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 جرب تاني", callback_data="new_calc")],
                [InlineKeyboardButton(text="🏦 جرب شهادات بنكية", callback_data="tool_bank")],
                [InlineKeyboardButton(text="🥇 جرب ذهب", callback_data="tool_gold")],
            ])
            await bot.send_message(
                chat_id,
                "❌ تعذر جلب أسعار الصرف حالياً\n\n"
                "ممكن تجرب أداة تانية أو تبدأ من جديد 👇",
                reply_markup=error_kb
            )
            await state.clear()
            return

        current_rate = hc["current_rate"]
        forecast_map = {"dur_6m": hc["forecast_6m"], "dur_1y": hc["forecast_1y"], "dur_3y": hc["forecast_3y"]}
        expected_rate = forecast_map[dur_key]

        dollars = amount / current_rate
        future_value = dollars * expected_rate
        profit = future_value - amount
        real_profit = profit - purchasing_loss

        result = (
            f"<b>💵 نتيجة الاستثمار في الدولار</b>\n"
            f"{PHARAOH_LINE}\n\n"
            f"{GOLD_DIAMOND} المبلغ: <b>{fmt(amount)} {currency_name}</b>\n"
            f"{GOLD_DIAMOND} المدة: <b>{dur_text}</b>\n\n"
            f"📊 <b>سعر لحظي:</b>\n"
            f"   الدولار الآن: <b>{fmt(current_rate)} {currency_name}</b>\n\n"
            f"🔮 <b>التوقعات</b> (تغير {hc['change_rate']}% سنوياً):\n"
            f"   السعر المتوقع بعد {dur_text}: <b>{fmt(expected_rate)} {currency_name}</b>\n\n"
            f"{'─' * 20}\n"
            f"💲 هتشتري: <b>{fmt(dollars)} دولار</b>\n"
            f"💵 القيمة المتوقعة: <b>{fmt(future_value)} {currency_name}</b>\n"
            f"📈 الربح المتوقع: <b>{fmt(profit)} {currency_name}</b>\n\n"
            f"{'─' * 20}\n"
            f"📉 <b>تأثير التضخم</b> {inflation_source}\n"
            f"{'─' * 20}\n\n"
            f"🔻 التضخم: <b>{inflation_rate}%</b> سنوياً\n"
            f"💸 خسارة القوة الشرائية: <b>{fmt(purchasing_loss)} {currency_name}</b>\n"
            f"✨ الربح الحقيقي: <b>{fmt(real_profit)} {currency_name}</b>\n\n"
        )
        result += _verdict(real_profit)

    result += f"\n<i>📢 النتائج تقديرية وليست نصيحة مالية</i>"

    btns = await result_buttons()
    await send_logo(chat_id, result, reply_markup=btns)
    await state.clear()


def _verdict(real_profit: float) -> str:
    if real_profit > 0:
        return f"✅ <b>استثمارك يتغلب على التضخم!</b> 🏆"
    else:
        return f"⚠️ <b>استثمارك لا يتغلب على التضخم</b>"


# ══════════════════════════════════════
#           لوحة تحكم الأدمن
# ══════════════════════════════════════

@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()

    users = await get_users_count()
    settings = await get_all_settings()
    by_country = await get_users_by_country()

    country_stats = "\n".join(
        [f"   {c or 'غير محدد'}: {n}" for c, n in by_country[:10]]
    ) if by_country else "   لا يوجد"

    text = (
        f"<b>⚙️ لوحة تحكم الأدمن</b>\n"
        f"{PHARAOH_LINE}\n\n"
        f"👥 المستخدمين: <b>{users}</b>\n"
        f"🌍 حسب الدولة:\n{country_stats}\n\n"
        f"<b>📊 الإعدادات:</b>\n"
        f"🥇 نمو الذهب السنوي: <b>{settings.get('gold_annual_growth', 10)}%</b>\n"
        f"💵 تغير العملة السنوي: <b>{settings.get('currency_annual_change', 8)}%</b>\n"
        f"📉 تضخم افتراضي: <b>{settings.get('fallback_inflation', 15)}%</b>\n"
        f"🔗 رابط: <a href=\"{settings.get('result_link_url', '#')}\">"
        f"{settings.get('result_link_text', 'الموقع')}</a>\n"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🥇 نمو الذهب السنوي %", callback_data="edit_gold_annual_growth")],
        [InlineKeyboardButton(text="💵 تغير العملة السنوي %", callback_data="edit_currency_annual_change")],
        [InlineKeyboardButton(text="📉 تضخم افتراضي %", callback_data="edit_fallback_inflation")],
        [InlineKeyboardButton(text="🔗 تعديل الرابط", callback_data="edit_result_link")],
        [InlineKeyboardButton(
            text="📢 رسالة جماعية",
            callback_data="admin_broadcast"
        )],
    ])

    await message.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML,
                         disable_web_page_preview=True)


@router.message(Command("myid"))
async def cmd_myid(message: Message):
    await message.answer(f"🆔 معرفك: <code>{message.from_user.id}</code>",
                         parse_mode=ParseMode.HTML)


SETTING_LABELS = {
    "gold_annual_growth": "نسبة نمو الذهب السنوية %",
    "currency_annual_change": "نسبة تغير العملة السنوية %",
    "fallback_inflation": "نسبة التضخم الافتراضية %",
}


@router.callback_query(F.data.startswith("edit_"))
async def edit_setting(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return

    key = callback.data.replace("edit_", "")

    if key == "result_link":
        await state.set_state(AdminStates.waiting_link_text)
        await callback.message.answer(
            "🔗 <b>تعديل الرابط</b>\n\nاكتب نص الزر الجديد:",
            parse_mode=ParseMode.HTML
        )
        return

    if key not in SETTING_LABELS:
        return

    current = await get_setting(key)
    await state.update_data(editing_key=key)
    await state.set_state(AdminStates.waiting_setting_value)
    await callback.message.answer(
        f"✏️ <b>{SETTING_LABELS[key]}</b>\n\n"
        f"القيمة الحالية: <b>{current}</b>\n\nاكتب القيمة الجديدة:",
        parse_mode=ParseMode.HTML
    )


@router.message(AdminStates.waiting_setting_value)
async def save_setting_value(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        value = float(message.text.strip())
    except ValueError:
        await message.answer("❌ أدخل رقم صحيح!")
        return

    data = await state.get_data()
    key = data["editing_key"]
    await set_setting(key, value)

    # تحديث config المباشر لو محتاج
    import config
    if key == "gold_annual_growth":
        config.DEFAULT_GOLD_ANNUAL_GROWTH = value
    elif key == "currency_annual_change":
        config.DEFAULT_CURRENCY_ANNUAL_CHANGE = value

    await state.clear()
    await message.answer(
        f"✅ تم تعديل <b>{SETTING_LABELS[key]}</b> إلى: <b>{value}</b>\n\n/admin",
        parse_mode=ParseMode.HTML
    )


@router.message(AdminStates.waiting_link_text)
async def edit_link_text(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await set_setting("result_link_text", message.text.strip())
    await state.set_state(AdminStates.waiting_link_url)
    await message.answer("✅ الآن اكتب الرابط (URL):")


@router.message(AdminStates.waiting_link_url)
async def edit_link_url(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    url = message.text.strip()
    if not (url.startswith("http://") or url.startswith("https://") or url.startswith("tg://")):
        await message.answer("❌ الرابط لازم يبدأ بـ http:// أو https://")
        return
    await set_setting("result_link_url", url)
    await state.clear()
    await message.answer("✅ تم تحديث الرابط!\n\n/admin")


# ── Broadcast ──

@router.callback_query(F.data == "admin_broadcast")
async def broadcast_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.waiting_broadcast_message)
    await callback.message.answer(
        "📢 <b>رسالة جماعية</b>\n\n"
        "اكتب الرسالة (يدعم HTML)\n/cancel للإلغاء",
        parse_mode=ParseMode.HTML
    )


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ تم الإلغاء")


@router.message(AdminStates.waiting_broadcast_message)
async def broadcast_send(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    user_ids = await get_all_user_ids()
    total = len(user_ids)
    success = failed = 0

    status = await message.answer(f"📤 جاري الإرسال لـ {total}...")

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
        f"✅ <b>تم الإرسال</b>\n\n📊 الإجمالي: {total}\n✅ نجاح: {success}\n❌ فشل: {failed}",
        parse_mode=ParseMode.HTML
    )


# ── Fallback ──

@router.message()
async def fallback(message: Message, state: FSMContext):
    current = await state.get_state()
    if current and "Admin" in current:
        return
    if current is None:
        is_sub = await check_subscription(message.from_user.id)
        if not is_sub:
            await message.answer("⚠️ اشترك في القناة!", reply_markup=sub_kb())
        else:
            await message.answer(f"اكتب /start عشان تبدأ {ANKH}")


# ══════════════════════════════════════
#              التشغيل
# ══════════════════════════════════════

async def on_startup(*args, **kwargs):
    await init_db()
    if USE_WEBHOOK:
        await bot.set_webhook(WEBHOOK_URL)
        logger.info(f"Webhook: {WEBHOOK_URL}")


async def on_shutdown(*args, **kwargs):
    if USE_WEBHOOK:
        try:
            await bot.delete_webhook()
        except Exception:
            pass
    await bot.session.close()


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
