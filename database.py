"""
قاعدة بيانات البوت v2 - SQLite
================================
"""
import aiosqlite
import json
import time
from config import DATABASE_PATH

DEFAULT_SETTINGS = {
    "result_link_text": "موقع اقتصاد أحمس",
    "result_link_url": "https://www.ahmoseeconomy.com/",
    "gold_annual_growth": 10.0,
    "currency_annual_change": 8.0,
    "fallback_inflation": 15.0,
}


async def init_db():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                country_code TEXT,
                currency TEXT,
                first_use REAL,
                last_use REAL,
                usage_count INTEGER DEFAULT 0,
                is_blocked INTEGER DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        await db.commit()
        for key, value in DEFAULT_SETTINGS.items():
            await db.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                (key, json.dumps(value))
            )
        await db.commit()


async def save_user(user_id: int, username: str = None,
                    first_name: str = None, last_name: str = None,
                    country_code: str = None, currency: str = None):
    now = time.time()
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            INSERT INTO users (user_id, username, first_name, last_name,
                             country_code, currency, first_use, last_use, usage_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name,
                last_name = excluded.last_name,
                country_code = COALESCE(excluded.country_code, country_code),
                currency = COALESCE(excluded.currency, currency),
                last_use = excluded.last_use,
                usage_count = usage_count + 1
        """, (user_id, username, first_name, last_name,
              country_code, currency, now, now))
        await db.commit()


async def get_user_country(user_id: int) -> tuple | None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "SELECT country_code, currency FROM users WHERE user_id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        if row and row[0]:
            return row[0], row[1]
    return None


async def get_all_user_ids() -> list:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "SELECT user_id FROM users WHERE is_blocked = 0"
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]


async def get_users_count() -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        row = await cursor.fetchone()
        return row[0]


async def get_users_by_country() -> list:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "SELECT country_code, COUNT(*) FROM users GROUP BY country_code ORDER BY COUNT(*) DESC"
        )
        return await cursor.fetchall()


async def block_user(user_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE users SET is_blocked = 1 WHERE user_id = ?", (user_id,)
        )
        await db.commit()


async def get_setting(key: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        )
        row = await cursor.fetchone()
        if row:
            return json.loads(row[0])
        return DEFAULT_SETTINGS.get(key)


async def set_setting(key: str, value):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, json.dumps(value))
        )
        await db.commit()


async def get_all_settings() -> dict:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("SELECT key, value FROM settings")
        rows = await cursor.fetchall()
        return {row[0]: json.loads(row[1]) for row in rows}
