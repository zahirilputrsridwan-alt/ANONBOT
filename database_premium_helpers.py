"""Database premium helpers and user account_type columns.
This updates the users table to include account_type, premium_start, premium_expired, premium_by
and provides helper functions to set/remove/check premium status and to return per-user limits.
"""
import aiosqlite
from datetime import datetime, timedelta
from config import DATABASE_PATH

async def ensure_premium_columns():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # check table info
        cur = await db.execute("PRAGMA table_info(users)")
        cols = await cur.fetchall()
        existing = {c[1] for c in cols}
        # add columns if missing
        if 'account_type' not in existing:
            await db.execute("ALTER TABLE users ADD COLUMN account_type TEXT DEFAULT 'free'")
        if 'premium_start' not in existing:
            await db.execute("ALTER TABLE users ADD COLUMN premium_start TEXT")
        if 'premium_expired' not in existing:
            await db.execute("ALTER TABLE users ADD COLUMN premium_expired TEXT")
        if 'premium_by' not in existing:
            await db.execute("ALTER TABLE users ADD COLUMN premium_by INTEGER")
        await db.commit()


async def set_premium(user_id: int, days: int | None, admin_id: int):
    """Set user premium. days=None means permanent (premium_expired NULL)."""
    await ensure_premium_columns()
    now = datetime.utcnow().isoformat()
    if days is None:
        expired = None
    else:
        expired = (datetime.utcnow() + timedelta(days=days)).isoformat()
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE users SET account_type = 'premium', premium_start = ?, premium_expired = ?, premium_by = ? WHERE user_id = ?",
            (now, expired, admin_id, user_id),
        )
        await db.commit()


async def remove_premium(user_id: int):
    await ensure_premium_columns()
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE users SET account_type = 'free', premium_start = NULL, premium_expired = NULL, premium_by = NULL WHERE user_id = ?",
            (user_id,)
        )
        await db.commit()


async def check_and_update_premium(user_id: int):
    """If user's premium expired, demote to free. Returns current account_type."""
    await ensure_premium_columns()
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT account_type, premium_expired FROM users WHERE user_id = ?", (user_id,))
        row = await cur.fetchone()
        if not row:
            return 'free'
        account_type, premium_expired = row
        if account_type != 'premium':
            return account_type
        if premium_expired is None:
            return 'premium'
        try:
            exp_dt = datetime.fromisoformat(premium_expired)
        except Exception:
            # invalid format: demote to free
            await remove_premium(user_id)
            return 'free'
        if datetime.utcnow() > exp_dt:
            await remove_premium(user_id)
            return 'free'
        return 'premium'


async def get_account_info(user_id: int):
    await ensure_premium_columns()
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT account_type, premium_start, premium_expired, premium_by FROM users WHERE user_id = ?", (user_id,))
        row = await cur.fetchone()
        if not row:
            return {'account_type': 'free', 'premium_start': None, 'premium_expired': None, 'premium_by': None}
        return {
            'account_type': row[0] or 'free',
            'premium_start': row[1],
            'premium_expired': row[2],
            'premium_by': row[3]
        }


async def get_user_limits(user_id: int):
    """Return limits dict based on account type. Unlimited can be represented by the string 'Unlimited'."""
    acct = await check_and_update_premium(user_id)
    if acct == 'premium':
        return {'messages': 'Unlimited', 'photos': 'Unlimited', 'videos': 'Unlimited', 'links': 'Unlimited'}
    # Free limits
    return {'messages': '10 / Hari', 'photos': '3 / Hari', 'videos': '1 / Hari', 'links': '3'}
