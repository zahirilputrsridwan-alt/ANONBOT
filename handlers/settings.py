from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from keyboards.home import main_reply_keyboard
from database import (
    ensure_user_settings, get_user_settings, update_user_setting,
    list_bad_words, add_bad_word, remove_bad_word, count_bad_words, get_statistics
)
import html

# Themes and language styles
THEMES = {
    "dark": "🌌 Dark",
    "ocean": "💙 Ocean",
    "purple": "💜 Purple",
    "emerald": "🟢 Emerald",
    "minimal": "🩶 Minimal",
}

LANG_STYLES = {
    "genz": "😎 Gen Z",
    "santai": "🙂 Santai",
    "formal": "🤝 Formal",
}

COOLDOWNS = [30, 60, 300, 600]

async def stats_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
        owner_id = query.from_user.id
    else:
        owner_id = update.effective_user.id

    stats = await get_statistics(owner_id)
    text = (
        "<b>📊 Statistik Akun</b>\n\n"
        f"📨 Total Pesan: <b>{stats['total_messages']}</b>\n"
        f"💬 Total Balasan: <b>{stats['total_replies']}</b>\n\n"
        f"📝 Pesan Teks: <b>{stats['text']}</b>\n"
        f"🖼️ Foto: <b>{stats['photo']}</b>\n"
        f"🎥 Video: <b>{stats['video']}</b>\n\n"
        f"📅 Bergabung: <b>{html.escape(stats['join_date'])}</b>"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Refresh", callback_data="stats_refresh")],
        [InlineKeyboardButton("⬅️ Kembali", callback_data="back_to_home")],
    ])
    if query:
        await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await context.bot.send_message(chat_id=owner_id, text=text, reply_markup=keyboard, parse_mode="HTML")


async def theme_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    owner_id = query.from_user.id
    text = "<b>🎨 Tema Bot</b>\n\nPilih tampilan favorit Anda."
    buttons = []
    for key, label in THEMES.items():
        buttons.append([InlineKeyboardButton(label, callback_data=f"theme_select:{key}")])
    buttons.append([InlineKeyboardButton("⬅️ Kembali", callback_data="back_to_home")])
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="HTML")


async def theme_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        _, key = query.data.split(":", 1)
    except Exception:
        await query.edit_message_text("Terjadi kesalahan.", parse_mode="HTML")
        return
    owner_id = query.from_user.id
    await update_user_setting(owner_id, "theme", key)
    text = f"✨ Tema disimpan: <b>{html.escape(THEMES.get(key, key))}</b>"
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali", callback_data="theme_menu")]])
    await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="HTML")


async def settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = "<b>⚙️ Pengaturan</b>\n\nSesuaikan pengalaman menggunakan bot."
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛡️ Anti Spam", callback_data="anti_spam")],
        [InlineKeyboardButton("☣️ Filter Kata Kasar", callback_data="filter_badwords")],
        [InlineKeyboardButton("🎭 Personalisasi", callback_data="personalization")],
        [InlineKeyboardButton("⬅️ Kembali", callback_data="back_to_home")],
    ])
    await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="HTML")


async def anti_spam_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    owner_id = query.from_user.id
    await ensure_user_settings(owner_id)
    settings = await get_user_settings(owner_id)
    anti = "🟢 Aktif" if settings[2] else "🔴 Nonaktif"
    cooldown = settings[3]
    auto_block = "✅ Ya" if settings[4] else "❌ Tidak"
    text = (
        "<b>🛡️ Anti Spam</b>\n\n"
        f"Status: <b>{anti}</b>\n"
        f"Cooldown: <b>{cooldown} detik</b>\n"
        f"Blokir Otomatis: <b>{auto_block}</b>\n\n"
        "Fitur mendeteksi: Flood Message, Spam Emoji, Spam Link, Pesan berulang.\n"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🟢 Aktif", callback_data="anti_spam_set:1"), InlineKeyboardButton("🔴 Nonaktif", callback_data="anti_spam_set:0")],
        [InlineKeyboardButton("⏳ Ubah Cooldown", callback_data="anti_spam_cooldown")],
        [InlineKeyboardButton("⬅️ Kembali", callback_data="settings")],
    ])
    await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="HTML")


async def anti_spam_set(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        _, val = query.data.split(":", 1)
        val = int(val)
    except Exception:
        await query.edit_message_text("Terjadi kesalahan.", parse_mode="HTML")
        return
    owner_id = query.from_user.id
    await update_user_setting(owner_id, "anti_spam", val)
    await anti_spam_menu(update, context)


async def anti_spam_cooldown_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    buttons = []
    for sec in COOLDOWNS:
        label = f"{sec//60} Menit" if sec >= 60 else f"{sec} Detik"
        buttons.append([InlineKeyboardButton(label, callback_data=f"anti_spam_set_cooldown:{sec}")])
    buttons.append([InlineKeyboardButton("⬅️ Kembali", callback_data="anti_spam")])
    await query.edit_message_text(text="<b>⏳ Pilih Cooldown</b>", reply_markup=InlineKeyboardMarkup(buttons), parse_mode="HTML")


async def anti_spam_set_cooldown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        _, sec = query.data.split(":", 1)
        sec = int(sec)
    except Exception:
        await query.edit_message_text("Terjadi kesalahan.", parse_mode="HTML")
        return
    owner_id = query.from_user.id
    await update_user_setting(owner_id, "cooldown", sec)
    await anti_spam_menu(update, context)


async def filter_badwords_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    owner_id = query.from_user.id
    await ensure_user_settings(owner_id)
    settings = await get_user_settings(owner_id)
    enabled = "🟢 Aktif" if settings[5] else "🔴 Nonaktif"
    count = await count_bad_words(owner_id)
    text = f"<b>☣️ Filter Kata Kasar</b>\n\nStatus: <b>{enabled}</b>\nJumlah Kata Terblokir: <b>{count}</b>\n\nJika aktif, bot akan menolak pesan yang mengandung kata blacklist."
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🟢 Aktif", callback_data="filter_set:1"), InlineKeyboardButton("🔴 Nonaktif", callback_data="filter_set:0")],
        [InlineKeyboardButton("📖 Lihat Daftar", callback_data="filter_view")],
        [InlineKeyboardButton("⬅️ Kembali", callback_data="settings")],
    ])
    await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="HTML")


async def filter_set(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        _, val = query.data.split(":", 1)
        val = int(val)
    except Exception:
        await query.edit_message_text("Terjadi kesalahan.", parse_mode="HTML")
        return
    owner_id = query.from_user.id
    await update_user_setting(owner_id, "filter_enabled", val)
    await filter_badwords_menu(update, context)


async def filter_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    owner_id = query.from_user.id
    words = await list_bad_words(owner_id)
    if not words:
        text = "<b>📖 Daftar Kata Terblokir</b>\n\nBelum ada kata yang diblokir."
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali", callback_data="filter_badwords")]])
        await query.edit_message_text(text=text, reply_markup=kb, parse_mode="HTML")
        return
    buttons = []
    for w in words:
        display = html.escape(w)
        buttons.append([InlineKeyboardButton(f"❌ Hapus — {display}", callback_data=f"filter_remove:{w}")])
    buttons.append([InlineKeyboardButton("➕ Tambah Kata", callback_data="filter_add")])
    buttons.append([InlineKeyboardButton("⬅️ Kembali", callback_data="filter_badwords")])
    text = "<b>📖 Daftar Kata Terblokir</b>\n\nKlik tombol untuk menghapus kata."
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="HTML")


async def filter_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        _, word = query.data.split(":", 1)
    except Exception:
        await query.edit_message_text("Terjadi kesalahan.", parse_mode="HTML")
        return
    owner_id = query.from_user.id
    await remove_bad_word(owner_id, word)
    await filter_view(update, context)


async def filter_add_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    owner_id = query.from_user.id
    context.user_data['awaiting_action'] = ("filter_add", owner_id)
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali", callback_data="filter_view")]])
    await query.edit_message_text(text="📥 Silakan kirim kata baru yang ingin diblokir (satu kata per pesan).", reply_markup=kb, parse_mode="HTML")


async def personalization_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    owner_id = query.from_user.id
    settings = await get_user_settings(owner_id)
    text = "<b>🎭 Personalisasi</b>\n\nSesuaikan gaya bot sesuai keinginan Anda."
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("😎 Gaya Bahasa", callback_data="personal_lang")],
        [InlineKeyboardButton("🎲 Pesan Acak", callback_data="personal_msg_random")],
        [InlineKeyboardButton("💌 Judul Acak", callback_data="personal_title_random")],
        [InlineKeyboardButton("✨ Emoji Premium", callback_data="personal_emoji")],
        [InlineKeyboardButton("⬅️ Kembali", callback_data="settings")],
    ])
    await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="HTML")


async def personal_lang_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    buttons = []
    for key, label in LANG_STYLES.items():
        buttons.append([InlineKeyboardButton(label, callback_data=f"personal_lang_set:{key}")])
    buttons.append([InlineKeyboardButton("⬅️ Kembali", callback_data="personalization")])
    await query.edit_message_text(text="<b>😎 Pilih Gaya Bahasa</b>", reply_markup=InlineKeyboardMarkup(buttons), parse_mode="HTML")


async def personal_lang_set(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        _, key = query.data.split(":", 1)
    except Exception:
        await query.edit_message_text("Terjadi kesalahan.", parse_mode="HTML")
        return
    owner_id = query.from_user.id
    await update_user_setting(owner_id, "language_style", key)
    await personalization_menu(update, context)


async def personal_toggle_setting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        _, field = query.data.split(":", 1)
    except Exception:
        await query.edit_message_text("Terjadi kesalahan.", parse_mode="HTML")
        return
    owner_id = query.from_user.id
    settings = await get_user_settings(owner_id)
    mapping = {"message_random":6, "title_random":7, "emoji_premium":8}
    if field not in mapping:
        await query.edit_message_text("Field tidak dikenali.", parse_mode="HTML")
        return
    cur_val = settings[mapping[field]]
    new_val = 0 if cur_val == 1 else 1
    await update_user_setting(owner_id, field, new_val)
    await personalization_menu(update, context)


async def handle_settings_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return False

    action = context.user_data.get('awaiting_action')
    if not action:
        return False

    act, owner_id = action
    if act == "filter_add":
        word = (update.message.text or "").strip()
        if not word:
            await update.message.reply_text("Kata kosong, coba lagi.", reply_markup=main_reply_keyboard())
            return True
        await add_bad_word(owner_id, word)
        await update.message.reply_text(f"✅ Kata '{word}' berhasil ditambahkan ke daftar blokir.", reply_markup=main_reply_keyboard())
        context.user_data.pop('awaiting_action', None)
        return True

    return False
