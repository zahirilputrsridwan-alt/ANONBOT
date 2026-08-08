import aiosqlite
import os
import sqlite3
from datetime import datetime, date, timedelta
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
              unique_code TEXT UNIQUE,
              personal_name TEXT DEFAULT '',
              personal_start_text TEXT DEFAULT '',
              personal_end_text TEXT DEFAULT ''
            );
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS links (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              owner_id INTEGER NOT NULL,
              unique_code TEXT UNIQUE,
              slug TEXT UNIQUE,
              name TEXT,
              start_text TEXT,
              end_text TEXT,
              status INTEGER DEFAULT 1,
              created_at TEXT
            );
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS link_settings (
              link_id INTEGER PRIMARY KEY,
              privacy INTEGER DEFAULT 0,
              web_preview INTEGER DEFAULT 1,
              formatting INTEGER DEFAULT 0,
              photo INTEGER DEFAULT 1,
              sticker INTEGER DEFAULT 1,
              video INTEGER DEFAULT 1,
              video_note INTEGER DEFAULT 1,
              audio INTEGER DEFAULT 1,
              voice INTEGER DEFAULT 1,
              document INTEGER DEFAULT 1,
              gif INTEGER DEFAULT 1,
              contact INTEGER DEFAULT 1,
              location INTEGER DEFAULT 1,
              FOREIGN KEY(link_id) REFERENCES links(id) ON DELETE CASCADE
            );
        """)

        # personal settings per user
        await db.execute("""
            CREATE TABLE IF NOT EXISTS personal_settings (
              owner_id INTEGER PRIMARY KEY,
              privacy INTEGER DEFAULT 0,
              web_preview INTEGER DEFAULT 1,
              formatting INTEGER DEFAULT 0,
              photo INTEGER DEFAULT 1,
              sticker INTEGER DEFAULT 1,
              video INTEGER DEFAULT 1,
              video_note INTEGER DEFAULT 1,
              audio INTEGER DEFAULT 1,
              voice INTEGER DEFAULT 1,
              document INTEGER DEFAULT 1,
              gif INTEGER DEFAULT 1,
              contact INTEGER DEFAULT 1,
              location INTEGER DEFAULT 1
            );
        """)

        # messages table for anonymous messages
        await db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              owner_id INTEGER,
              link_code TEXT,
              sender_chat_id INTEGER,
              message_type TEXT,
              content TEXT,
              file_id TEXT,
              created_at TEXT
            );
        """)

        # user_settings per-user
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
              owner_id INTEGER PRIMARY KEY,
              theme TEXT DEFAULT 'dark',
              anti_spam INTEGER DEFAULT 0,
              cooldown INTEGER DEFAULT 30,
              auto_block INTEGER DEFAULT 0,
              filter_enabled INTEGER DEFAULT 0,
              message_random INTEGER DEFAULT 1,
              title_random INTEGER DEFAULT 1,
              emoji_premium INTEGER DEFAULT 0,
              language_style TEXT DEFAULT 'genz'
            );
        """)

        # bad words blacklist per user
        await db.execute("""
            CREATE TABLE IF NOT EXISTS bad_words (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              owner_id INTEGER,
              word TEXT
            );
        """)

        # admin logs
        await db.execute("""
            CREATE TABLE IF NOT EXISTS admin_logs (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              level TEXT,
              action TEXT,
              detail TEXT,
              created_at TEXT
            );
        """)

        # banned users
        await db.execute("""
            CREATE TABLE IF NOT EXISTS banned_users (
              user_id INTEGER PRIMARY KEY,
              reason TEXT,
              banned_at TEXT
            );
        """)

        # bot settings (global)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS bot_settings (
              key TEXT PRIMARY KEY,
              value TEXT
            );
        """)

        # global stats counters (simple kv)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS global_stats (
              key TEXT PRIMARY KEY,
              value INTEGER DEFAULT 0
            );
        """)

        await db.commit()

# ------------------ users & links (existing helpers) ------------------
async def add_user_if_not_exists(user_id, first_name, username, join_date):
    """Insert user if not exists. Returns the unique_code (existing or newly created)."""
    import secrets
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT unique_code FROM users WHERE user_id = ?", (user_id,))
        row = await cur.fetchone()
        if row:
            # ensure personal settings exists
            await db.execute("INSERT OR IGNORE INTO personal_settings (owner_id) VALUES (?)", (user_id,))
            await db.execute("INSERT OR IGNORE INTO user_settings (owner_id) VALUES (?)", (user_id,))
            await db.commit()
            return row[0]

        # try to insert a unique code
        for _ in range(5):
            code = secrets.token_urlsafe(8)
            try:
                await db.execute(
                    "INSERT INTO users (user_id, first_name, username, join_date, unique_code) VALUES (?,?,?,?,?)",
                    (user_id, first_name, username, join_date, code),
                )
                await db.execute("INSERT OR IGNORE INTO personal_settings (owner_id) VALUES (?)", (user_id,))
                await db.execute("INSERT OR IGNORE INTO user_settings (owner_id) VALUES (?)", (user_id,))
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
        await db.execute("INSERT OR IGNORE INTO personal_settings (owner_id) VALUES (?)", (user_id,))
        await db.execute("INSERT OR IGNORE INTO user_settings (owner_id) VALUES (?)", (user_id,))
        await db.commit()
        return code

async def get_user(user_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT user_id, first_name, username, join_date, unique_code, personal_name, personal_start_text, personal_end_text FROM users WHERE user_id = ?", (user_id,))
        row = await cur.fetchone()
        return row

async def get_user_by_code(unique_code: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT user_id, first_name, username, join_date, unique_code, personal_name, personal_start_text, personal_end_text FROM users WHERE unique_code = ?", (unique_code,))
        row = await cur.fetchone()
        return row

# ------------------ links & messages ------------------
async def create_link(owner_id: int, name: str, created_at: str, slug: str = None):
    import secrets
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # generate unique_code
        for _ in range(10):
            code = secrets.token_urlsafe(8)
            try:
                if slug is None:
                    slug_candidate = code
                else:
                    slug_candidate = slug
                await db.execute(
                    "INSERT INTO links (owner_id, unique_code, slug, name, start_text, end_text, status, created_at) VALUES (?,?,?,?,?,?,?,?)",
                    (owner_id, code, slug_candidate, name, '', '', 1, created_at),
                )
                await db.commit()
                cur = await db.execute("SELECT id FROM links WHERE unique_code = ?", (code,))
                row = await cur.fetchone()
                link_id = row[0]

                # create default settings
                await db.execute(
                    "INSERT INTO link_settings (link_id) VALUES (?)",
                    (link_id,),
                )
                await db.commit()
                return link_id, code
            except sqlite3.IntegrityError:
                continue
        # fallback
        code = str(owner_id) + '_' + secrets.token_hex(4)
        await db.execute(
            "INSERT OR IGNORE INTO links (owner_id, unique_code, slug, name, start_text, end_text, status, created_at) VALUES (?,?,?,?,?,?,?,?)",
            (owner_id, code, code, name, '', '', 1, created_at),
        )
        await db.commit()
        cur = await db.execute("SELECT id FROM links WHERE unique_code = ?", (code,))
        row = await cur.fetchone()
        link_id = row[0]
        await db.execute("INSERT OR IGNORE INTO link_settings (link_id) VALUES (?)", (link_id,))
        await db.commit()
        return link_id, code

async def get_links_by_owner(owner_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT id, name, unique_code, slug, status, created_at FROM links WHERE owner_id = ? ORDER BY id DESC", (owner_id,))
        rows = await cur.fetchall()
        return rows

async def get_link_by_id(link_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT id, owner_id, unique_code, slug, name, start_text, end_text, status, created_at FROM links WHERE id = ?", (link_id,))
        row = await cur.fetchone()
        return row

async def get_link_settings(link_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT * FROM link_settings WHERE link_id = ?", (link_id,))
        row = await cur.fetchone()
        return row

async def update_link_name(link_id: int, new_name: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE links SET name = ? WHERE id = ?", (new_name, link_id))
        await db.commit()

async def toggle_link_status(link_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT status FROM links WHERE id = ?", (link_id,))
        row = await cur.fetchone()
        if not row:
            return None
        new = 0 if row[0] == 1 else 1
        await db.execute("UPDATE links SET status = ? WHERE id = ?", (new, link_id))
        await db.commit()
        return new

async def update_setting(link_id: int, field: str, value: int):
    allowed = {"privacy", "web_preview", "formatting", "photo", "sticker", "video", "video_note", "audio", "voice", "document", "gif", "contact", "location"}
    if field not in allowed:
        raise ValueError("Invalid setting")
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(f"UPDATE link_settings SET {field} = ? WHERE link_id = ?", (int(value), link_id))
        await db.commit()

async def count_messages_for_link(link_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT COUNT(1) FROM messages WHERE link_code = (SELECT unique_code FROM links WHERE id = ?)", (link_id,))
        row = await cur.fetchone()
        return row[0] if row else 0

async def count_messages_for_user(user_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT COUNT(1) FROM messages WHERE owner_id = ?", (user_id,))
        row = await cur.fetchone()
        return row[0] if row else 0

async def get_owner_by_code(unique_code: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT user_id FROM users WHERE unique_code = ?", (unique_code,))
        row = await cur.fetchone()
        if row:
            return row[0]
        cur = await db.execute("SELECT owner_id FROM links WHERE unique_code = ?", (unique_code,))
        row = await cur.fetchone()
        return row[0] if row else None

async def add_message(owner_id: int, link_code: str, message_type: str, content: str = None, file_id: str = None, created_at: str = None, sender_chat_id: int = None):
    created_at = created_at or datetime.utcnow().isoformat()
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT INTO messages (owner_id, link_code, sender_chat_id, message_type, content, file_id, created_at) VALUES (?,?,?,?,?,?,?)",
            (owner_id, link_code, sender_chat_id, message_type, content, file_id, created_at)
        )
        await db.commit()

# ------------------ user settings, bad words, statistics ------------------
async def ensure_user_settings(owner_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO user_settings (owner_id) VALUES (?)", (owner_id,))
        await db.commit()

async def get_user_settings(owner_id: int):
    await ensure_user_settings(owner_id)
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT owner_id, theme, anti_spam, cooldown, auto_block, filter_enabled, message_random, title_random, emoji_premium, language_style FROM user_settings WHERE owner_id = ?", (owner_id,))
        row = await cur.fetchone()
        return row

async def update_user_setting(owner_id: int, field: str, value):
    allowed = {"theme","anti_spam","cooldown","auto_block","filter_enabled","message_random","title_random","emoji_premium","language_style"}
    if field not in allowed:
        raise ValueError("Invalid user setting")
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(f"UPDATE user_settings SET {field} = ? WHERE owner_id = ?", (value, owner_id))
        await db.commit()

# bad words per user
async def add_bad_word(owner_id: int, word: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("INSERT INTO bad_words (owner_id, word) VALUES (?,?)", (owner_id, word))
        await db.commit()

async def remove_bad_word(owner_id: int, word: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM bad_words WHERE owner_id = ? AND word = ?", (owner_id, word))
        await db.commit()

async def list_bad_words(owner_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT word FROM bad_words WHERE owner_id = ?", (owner_id,))
        rows = await cur.fetchall()
        return [r[0] for r in rows]

async def count_bad_words(owner_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT COUNT(1) FROM bad_words WHERE owner_id = ?", (owner_id,))
        row = await cur.fetchone()
        return row[0] if row else 0

async def get_statistics(owner_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT COUNT(1) FROM messages WHERE owner_id = ?", (owner_id,))
        total_msgs = (await cur.fetchone())[0]
        cur = await db.execute("SELECT COUNT(1) FROM messages WHERE owner_id = ? AND message_type = 'reply'", (owner_id,))
        total_replies = (await cur.fetchone())[0]
        cur = await db.execute("SELECT message_type, COUNT(1) FROM messages WHERE owner_id = ? GROUP BY message_type", (owner_id,))
        rows = await cur.fetchall()
        types = {r[0]: r[1] for r in rows}
        text_count = types.get('text', 0)
        photo_count = types.get('photo', 0)
        video_count = types.get('video', 0)
        cur = await db.execute("SELECT join_date FROM users WHERE user_id = ?", (owner_id,))
        row = await cur.fetchone()
        join_date = row[0] if row else "-"
        return {
            'total_messages': total_msgs,
            'total_replies': total_replies,
            'text': text_count,
            'photo': photo_count,
            'video': video_count,
            'join_date': join_date
        }

# ------------------ admin functions & global stats ------------------
async def add_admin_log(level: str, action: str, detail: str = None):
    created_at = datetime.utcnow().isoformat()
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("INSERT INTO admin_logs (level, action, detail, created_at) VALUES (?,?,?,?)", (level, action, detail, created_at))
        await db.commit()

async def get_admin_logs(limit: int = 50):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT id, level, action, detail, created_at FROM admin_logs ORDER BY id DESC LIMIT ?", (limit,))
        rows = await cur.fetchall()
        return rows

async def ban_user(user_id: int, reason: str = None):
    banned_at = datetime.utcnow().isoformat()
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO banned_users (user_id, reason, banned_at) VALUES (?,?,?)", (user_id, reason, banned_at))
        await db.commit()
    await add_admin_log('info', 'ban', f"user_id={user_id} reason={reason}")

async def unban_user(user_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM banned_users WHERE user_id = ?", (user_id,))
        await db.commit()
    await add_admin_log('info', 'unban', f"user_id={user_id}")

async def is_user_banned(user_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT user_id FROM banned_users WHERE user_id = ?", (user_id,))
        row = await cur.fetchone()
        return bool(row)

async def get_total_users():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT COUNT(1) FROM users")
        row = await cur.fetchone()
        return row[0] if row else 0

async def get_total_messages():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT COUNT(1) FROM messages")
        row = await cur.fetchone()
        return row[0] if row else 0

async def get_total_replies():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT COUNT(1) FROM messages WHERE message_type = 'reply'")
        row = await cur.fetchone()
        return row[0] if row else 0

async def get_total_by_type(msg_type: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT COUNT(1) FROM messages WHERE message_type = ?", (msg_type,))
        row = await cur.fetchone()
        return row[0] if row else 0

async def get_users_new_today():
    today = date.today().isoformat()
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT COUNT(1) FROM users WHERE substr(join_date,1,10) = ?", (today,))
        row = await cur.fetchone()
        return row[0] if row else 0

async def get_messages_today():
    today = date.today().isoformat()
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT COUNT(1) FROM messages WHERE substr(created_at,1,10) = ?", (today,))
        row = await cur.fetchone()
        return row[0] if row else 0

async def get_all_user_ids():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT user_id FROM users")
        rows = await cur.fetchall()
        return [r[0] for r in rows]

async def update_bot_setting(key: str, value: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO bot_settings (key, value) VALUES (?,?)", (key, value))
        await db.commit()
    await add_admin_log('info', 'bot_setting_update', f"{key}={value}")

async def get_bot_setting(key: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT value FROM bot_settings WHERE key = ?", (key,))
        row = await cur.fetchone()
        return row[0] if row else None

# ------------------ utility for broadcast logging ------------------
async def increment_global_stat(key: str, delta: int = 1):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT value FROM global_stats WHERE key = ?", (key,))
        row = await cur.fetchone()
        if row:
            new = row[0] + delta
            await db.execute("UPDATE global_stats SET value = ? WHERE key = ?", (new, key))
        else:
            await db.execute("INSERT INTO global_stats (key, value) VALUES (?,?)", (key, delta))
        await db.commit()

async def get_global_stats():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT key, value FROM global_stats")
        rows = await cur.fetchall()
        return {r[0]: r[1] for r in rows}
