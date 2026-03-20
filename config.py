"""
إعدادات بوت اقتصاد أحمس v2
=============================
"""
import os

# ===== البوت =====
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# ===== القناة =====
CHANNEL_USERNAME = "@ahmoseeconomy"
CHANNEL_LINK = "https://t.me/ahmoseeconomy"

# ===== الأدمن =====
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "0").split(",") if x.strip()]

# ===== Webhook =====
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "https://yourdomain.com")
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", 8443))
USE_WEBHOOK = os.getenv("USE_WEBHOOK", "false").lower() == "true"

# ===== قاعدة البيانات =====
DATABASE_PATH = os.getenv("DATABASE_PATH", "bot_database.db")

# ===== اللوجو =====
LOGO_PATH = os.path.join(os.path.dirname(__file__), "logo.png")

# ===== APIs (مجانية بدون مفتاح) =====
EXCHANGE_RATE_API = "https://open.er-api.com/v6/latest/{base}"
GOLD_API_URL = "https://data-asg.goldprice.org/dbXRates/USD"
WORLD_BANK_INFLATION_API = (
    "https://api.worldbank.org/v2/country/{code}/indicator/"
    "FP.CPI.TOTL.ZG?format=json&per_page=3&mrv=3"
)

# ===== التوقعات الافتراضية (نسب سنوية) =====
DEFAULT_GOLD_ANNUAL_GROWTH = 8.0    # متوسط نمو الذهب سنوياً % (بناءً على أداء الذهب آخر 20 سنة تقريباً)
DEFAULT_CURRENCY_ANNUAL_CHANGE = 8.0  # متوسط تغير العملة سنوياً %

# ===== سعر الذهب الاحتياطي (لو كل الـ APIs فشلت) =====
# سعر جرام الذهب بالدولار - حدّثه يدوياً كل فترة
FALLBACK_GOLD_PRICE_USD = float(os.getenv("FALLBACK_GOLD_PRICE_USD", "93.0"))  # سعر جرام ذهب عيار 24 تقريبي
