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
              message_type TEXT,
              content TEXT,
              file_id TEXT,
              created_at TEXT
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
            # ensure personal settings exists
            await db.execute("INSERT OR IGNORE INTO personal_settings (owner_id) VALUES (?)", (user_id,))
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
        await db.commit()
        return code

# --- Links related DB functions ---
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
    # Placeholder: no messages table yet
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT COUNT(1) FROM messages WHERE link_code = (SELECT unique_code FROM links WHERE id = ?)", (link_id,))
        row = await cur.fetchone()
        return row[0] if row else 0

# --- Personal link functions ---
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

async def update_user_personal_name(user_id: int, new_name: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE users SET personal_name = ? WHERE user_id = ?", (new_name, user_id))
        await db.commit()

async def update_user_personal_start_text(user_id: int, text: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE users SET personal_start_text = ? WHERE user_id = ?", (text, user_id))
        await db.commit()

async def update_user_personal_end_text(user_id: int, text: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE users SET personal_end_text = ? WHERE user_id = ?", (text, user_id))
        await db.commit()

async def get_personal_settings(owner_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT * FROM personal_settings WHERE owner_id = ?", (owner_id,))
        row = await cur.fetchone()
        return row

async def update_personal_setting(owner_id: int, field: str, value: int):
    allowed = {"privacy", "web_preview", "formatting", "photo", "sticker", "video", "video_note", "audio", "voice", "document", "gif", "contact", "location"}
    if field not in allowed:
        raise ValueError("Invalid setting")
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(f"UPDATE personal_settings SET {field} = ? WHERE owner_id = ?", (int(value), owner_id))
        await db.commit()

async def count_messages_for_user(user_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT COUNT(1) FROM messages WHERE owner_id = ?", (user_id,))
        row = await cur.fetchone()
        return row[0] if row else 0

async def get_owner_by_code(unique_code: str):
    """Return owner_id if unique_code belongs to user or link, else None."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT user_id FROM users WHERE unique_code = ?", (unique_code,))
        row = await cur.fetchone()
        if row:
            return row[0]
        cur = await db.execute("SELECT owner_id FROM links WHERE unique_code = ?", (unique_code,))
        row = await cur.fetchone()
        return row[0] if row else None

async def add_message(owner_id: int, link_code: str, message_type: str, content: str = None, file_id: str = None, created_at: str = None):
    created_at = created_at or datetime.utcnow().isoformat()
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT INTO messages (owner_id, link_code, message_type, content, file_id, created_at) VALUES (?,?,?,?,?,?)",
            (owner_id, link_code, message_type, content, file_id, created_at)
        )
        await db.commit()
