import aiosqlite
import os
import sqlite3
from config import DATABASE_PATH

async def init_db():
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
              user_id INTEGER PRIMARY KEY,
              first_name TEXT,
              username TEXT,
              join_date TEXT,
              unique_code TEXT UNIQUE
            );
        """)
        await db.commit()

async def add_user_if_not_exists(user_id, first_name, username, join_date):
    """Insert user if not exists. Returns the unique_code (existing or newly created)."""
    import secrets
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT unique_code FROM users WHERE user_id = ?", (user_id,))
        row = await cur.fetchone()
        if row:
            return row[0]

        # try to insert a unique code
        for _ in range(5):
            code = secrets.token_urlsafe(8)
            try:
                await db.execute(
                    "INSERT INTO users (user_id, first_name, username, join_date, unique_code) VALUES (?,?,?,?,?)",
                    (user_id, first_name, username, join_date, code),
                )
                await db.commit()
                return code
            except sqlite3.IntegrityError:
                # unique_code conflict, try again
                continue

        # fallback: use user_id as code (should be unique)
        code = str(user_id)
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, first_name, username, join_date, unique_code) VALUES (?,?,?,?,?)",
            (user_id, first_name, username, join_date, code),
        )
        await db.commit()
        return code
