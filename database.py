
# --- Statistics & User Settings helpers ---
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

# statistics
async def get_statistics(owner_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # total messages sent to owner
        cur = await db.execute("SELECT COUNT(1) FROM messages WHERE owner_id = ?", (owner_id,))
        total_msgs = (await cur.fetchone())[0]
        # total replies by owner
        cur = await db.execute("SELECT COUNT(1) FROM messages WHERE owner_id = ? AND message_type = 'reply'", (owner_id,))
        total_replies = (await cur.fetchone())[0]
        # by type
        cur = await db.execute("SELECT message_type, COUNT(1) FROM messages WHERE owner_id = ? GROUP BY message_type", (owner_id,))
        rows = await cur.fetchall()
        types = {r[0]: r[1] for r in rows}
        text_count = types.get('text', 0)
        photo_count = types.get('photo', 0)
        video_count = types.get('video', 0)
        # join date
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
