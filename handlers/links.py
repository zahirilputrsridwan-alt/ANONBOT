from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import (
    create_link, get_links_by_owner, get_link_by_id, get_link_settings,
    toggle_link_status, update_setting, count_messages_for_link, update_link_name,
    get_user, get_personal_settings, update_personal_setting, count_messages_for_user
)
from datetime import datetime

# --- Manage links handler (unchanged flows retained) ---
async def handle_manage_links_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    data = query.data or ""
    chat_id = query.message.chat.id
    message_id = query.message.message_id

    # store current menu message so text inputs can edit it
    context.user_data['menu_message'] = (chat_id, message_id)

    if data == "manage_links":
        text = "🗂️ <b>Pengelolaan Tautan</b>\n\nDi menu ini Anda dapat membuat dan mengelola beberapa tautan anonim.\n\nSetiap tautan memiliki pengaturan masing-masing seperti:\n\n• Nama tautan\n• Teks pembuka\n• Teks penutup\n• Status aktif/nonaktif\n• Pengaturan media\n• Pengaturan fitur\n"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Tambahkan Tautan Baru", callback_data="add_new_link")],
            [InlineKeyboardButton("📂 Daftar Tautan", callback_data="list_links")],
            [InlineKeyboardButton("⬅️ Kembali", callback_data="back_to_home")],
        ])
        await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="HTML")
        return

    if data == "add_new_link":
        # prompt for name
        context.user_data['awaiting_link_name'] = True
        text = "💬 Masukkan nama tautan yang ingin dibuat."
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali", callback_data="manage_links")]])
        await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="HTML")
        return

    if data == "list_links":
        owner = query.from_user.id
        rows = await get_links_by_owner(owner)
        if not rows:
            text = "📂 Anda belum memiliki tautan tambahan."
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali", callback_data="manage_links")]])
            await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="HTML")
            return
        # build buttons for each link
        buttons = []
        for r in rows:
            lid, name, unique_code, slug, status, created_at = r
            label = f"{name} ({'✅' if status==1 else '❌'})"
            buttons.append([InlineKeyboardButton(label, callback_data=f"link_settings:{lid}")])
        buttons.append([InlineKeyboardButton("⬅️ Kembali", callback_data="manage_links")])
        await query.edit_message_text(text="📂 Daftar Tautan Anda:", reply_markup=InlineKeyboardMarkup(buttons), parse_mode="HTML")
        return

    # link specific settings
    if data.startswith("link_settings:"):
        try:
            lid = int(data.split(":",1)[1])
        except Exception:
            await query.answer("Invalid link")
            return
        row = await get_link_by_id(lid)
        if not row:
            await query.answer("Tautan tidak ditemukan")
            return
        idd, owner_id, unique_code, slug, name, start_text, end_text, status, created_at = row
        count = await count_messages_for_link(idd)
        text = f"<b>{name}</b>\n\nJumlah pesan diterima: {count}\nTanggal dibuat: {created_at}\nStatus: {'✅ Aktif' if status==1 else '❌ Nonaktif'}\nLink tautan:\nhttps://t.me/{context.bot.username}?start={unique_code}"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⚙️ Pengaturan", callback_data=f"general:{idd}"), InlineKeyboardButton("🗑 Cabut Tautan", callback_data=f"link_delete:{idd}")],
            [InlineKeyboardButton("📤 Bagikan", callback_data=f"link_share:{idd}"), InlineKeyboardButton("📋 Salin Tautan", callback_data=f"link_copy:{idd}")],
            [InlineKeyboardButton("⬅️ Kembali", callback_data="list_links")]
        ])
        await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="HTML", disable_web_page_preview=True)
        return

    # general menu for created links
    if data.startswith("general:"):
        lid = int(data.split(":",1)[1])
        row = await get_link_by_id(lid)
        if not row:
            await query.answer("Tautan tidak ditemukan")
            return
        idd, owner_id, unique_code, slug, name, start_text, end_text, status, created_at = row
        text = f"<b>⚙️ Pengaturan — {name}</b>\n\nNama tautan: {name}\nJumlah pesan diterima: {await count_messages_for_link(idd)}\nTanggal dibuat: {created_at}\nStatus: {'✅ Aktif' if status==1 else '❌ Nonaktif'}\nLink tautan:\nhttps://t.me/{context.bot.username}?start={unique_code}"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 Sesuaikan Alamat Tautan", callback_data=f"adjust_slug:{idd}"), InlineKeyboardButton("✏️ Ganti Nama", callback_data=f"change_name:{idd}")],
            [InlineKeyboardButton(f"Status: {'✅ Aktif' if status==1 else '❌ Nonaktif'}", callback_data=f"toggle_status:{idd}")],
            [InlineKeyboardButton("💬 Ubah Teks Awal", callback_data=f"change_start_text:{idd}"), InlineKeyboardButton("💬 Ubah Teks Akhir", callback_data=f"change_end_text:{idd}")],
            [InlineKeyboardButton("🗑 Cabut Tautan", callback_data=f"link_delete:{idd}"), InlineKeyboardButton("📤 Bagikan", callback_data=f"link_share:{idd}")],
            [InlineKeyboardButton("⬅️ Kembali", callback_data=f"link_settings:{idd}")]
        ])
        await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="HTML", disable_web_page_preview=True)
        return

    # toggle status
    if data.startswith("toggle_status:"):
        lid = int(data.split(":",1)[1])
        new = await toggle_link_status(lid)
        # refresh general menu
        await handle_manage_links_callback(update, context)
        return

    # change / adjust flows (left as in previous implementation)
    if data.startswith("change_name:") or data.startswith("adjust_slug:") or data.startswith("change_start_text:") or data.startswith("change_end_text:"):
        parts = data.split(":",1)
        action = parts[0]
        lid = int(parts[1])
        context.user_data['awaiting_action'] = (action, lid)
        prompt = {
            'change_name': "✏️ Silakan kirim nama baru untuk tautan ini.",
            'adjust_slug': "🔗 Silakan kirim slug/alamat baru (tanpa spasi).",
            'change_start_text': "💬 Silakan kirim teks pembuka baru.",
            'change_end_text': "💬 Silakan kirim teks penutup baru.",
        }[action]
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali", callback_data=f"general:{lid}")]])
        await query.edit_message_text(text=prompt, reply_markup=keyboard, parse_mode="HTML")
        return

    # link delete/share/copy placeholders
    if data.startswith("link_delete:"):
        lid = int(data.split(":",1)[1])
        # mark privacy=1 as a simple marker
        await update_setting(lid, 'privacy', 1)
        text = "✅ Tautan dicabut."
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali", callback_data="manage_links")]])
        await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="HTML")
        return

    if data.startswith("link_share:") or data.startswith("link_copy:"):
        lid = int(data.split(":",1)[1])
        row = await get_link_by_id(lid)
        if not row:
            await query.answer("Tautan tidak ditemukan")
            return
        idd, owner_id, unique_code, slug, name, start_text, end_text, status, created_at = row
        text = f"Nama:\n{name}\n\nTautan:\nhttps://t.me/{context.bot.username}?start={unique_code}\n\nTautan tersebut dapat dibagikan ke Telegram, Instagram, TikTok, maupun media sosial lainnya."
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⚙️ Pengaturan", callback_data=f"general:{idd}"), InlineKeyboardButton("🗑 Cabut Tautan", callback_data=f"link_delete:{idd}")],
            [InlineKeyboardButton("⬅️ Kembali", callback_data=f"list_links")]
        ])
        await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="HTML", disable_web_page_preview=True)
        return

    # settings toggles (media/features)
    if data.startswith("setting_"):
        try:
            _, rest = data.split("setting_",1)
            field, lid = rest.split(":",1)
            lid = int(lid)
        except Exception:
            await query.answer("Invalid setting")
            return
        settings = await get_link_settings(lid)
        if not settings:
            await query.answer("Settings not found")
            return
        cols = ["link_id","privacy","web_preview","formatting","photo","sticker","video","video_note","audio","voice","document","gif","contact","location"]
        if field not in cols:
            await query.answer("Unknown field")
            return
        idx = cols.index(field)
        cur_val = settings[idx]
        new_val = 0 if cur_val==1 else 1
        await update_setting(lid, field, new_val)
        await handle_manage_links_callback(update, context)
        return

    # fallback
    await query.edit_message_text(text="🚧 Menu ini masih dalam tahap pengembangan.", parse_mode="HTML")


# --- Personal link handler (updated to NOT reveal owner identity) ---
async def handle_personal_link_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    data = query.data or ""
    chat_id = query.message.chat.id
    message_id = query.message.message_id

    # store current menu message so text inputs can edit it
    context.user_data['menu_message'] = (chat_id, message_id)

    user = query.from_user
    owner_id = user.id

    # Top-level "my link" page
    if data == "my_link":
        user_row = await get_user(owner_id)
        if not user_row:
            await query.edit_message_text(text="⚠️ Terjadi kesalahan: data pengguna tidak ditemukan.", parse_mode="HTML")
            return
        # user_row: user_id, first_name, username, join_date, unique_code, personal_name, personal_start_text, personal_end_text
        # We MUST NOT display any owner identity (first_name/username/photo). Only show link and generic text.
        _, _, _, join_date, unique_code, _, _, _ = user_row
        bot_username = context.bot.username or "your_bot"
        personal_link = f"https://t.me/{bot_username}?start={unique_code}"
        text = (
            "🔗 <b>Tautan Pribadi Gua</b>\n\n"
            f"<code>{personal_link}</code>\n\n"
            "⬇️ 1. Gercep Salin Link: Tinggal salin tautan di atas, terus langsung templokin ke bio IG, TikTok, atau sosmed kesayangan lu!\n\n"
            "☕ 2. Pamer Lewat Tombol Bagikan: Mau ngajak mutualan atau temen tongkrongan nge-spill? Tinggal cocol tombol Bagikan di bawah.\n\n"
            "🥷 3. Masuk Senyap Tanpa Jejak: Semua unek-unek atau rahasia pedes dari mereka bakal otomatis masuk diem-diem ke bot lu, aman pol!\n\n"
            "✨ 4. Bebas Tebar Di Mana Aja: Mau dipajang di Insta Story, X (Twitter), atau grup manapun, dijamin tinggal cocol link-nya langsung gaskeun.\n"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⚙️ Pengaturan", callback_data="personal_settings")],
            [InlineKeyboardButton("📤 Bagikan", callback_data="personal_share"), InlineKeyboardButton("📋 Salin Tautan", callback_data="personal_copy")],
            [InlineKeyboardButton("⬅️ Kembali", callback_data="back_to_home")],
        ])
        await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="HTML", disable_web_page_preview=True)
        return

    # Personal settings main menu
    if data == "personal_settings":
        user_row = await get_user(owner_id)
        if not user_row:
            await query.edit_message_text(text="⚠️ Data pengguna tidak ditemukan.", parse_mode="HTML")
            return
        uid, _, _, join_date, unique_code, _, _, _ = user_row
        count = await count_messages_for_user(uid)
        bot_username = context.bot.username or "your_bot"
        personal_link = f"https://t.me/{bot_username}?start={unique_code}"
        text = (
            "🔗 <b>Tautan Pribadi</b>\n\n"
            f"📨 Jumlah pesan diterima: {count}\n"
            f"📅 Tanggal dibuat: {join_date}\n\n"
            f"🔗 Link tautan:\n<code>{personal_link}</code>\n"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🖼️ Media", callback_data="personal_media"), InlineKeyboardButton("✨ Fitur", callback_data="personal_features")],
            [InlineKeyboardButton("📤 Bagikan", callback_data="personal_share"), InlineKeyboardButton("📋 Salin Tautan", callback_data="personal_copy")],
            [InlineKeyboardButton("⬅️ Kembali", callback_data="my_link")],
        ])
        await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="HTML", disable_web_page_preview=True)
        return

    # Personal share / copy
    if data in ("personal_share", "personal_copy"):
        user_row = await get_user(owner_id)
        if not user_row:
            await query.edit_message_text(text="⚠️ Data pengguna tidak ditemukan.", parse_mode="HTML")
            return
        uid, _, _, _, unique_code, _, _, _ = user_row
        bot_username = context.bot.username or "your_bot"
        link = f"https://t.me/{bot_username}?start={unique_code}"
        text = f"🔗 Tautan pribadi Anda:\n<code>{link}</code>\n\nTautan tersebut dapat dibagikan ke Telegram, Instagram, TikTok, maupun media sosial lainnya."
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⚙️ Pengaturan", callback_data="personal_settings")],
            [InlineKeyboardButton("⬅️ Kembali", callback_data="my_link")],
        ])
        await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="HTML", disable_web_page_preview=True)
        return

    # Personal Media Menu
    if data == "personal_media":
        settings = await get_personal_settings(owner_id)
        if not settings:
            await query.edit_message_text(text="⚠️ Pengaturan personal tidak ditemukan.", parse_mode="HTML")
            return
        cols = ["owner_id","privacy","web_preview","formatting","photo","sticker","video","video_note","audio","voice","document","gif","contact","location"]
        media_fields = ["photo","sticker","video","video_note","audio","voice","document","gif","contact","location"]
        buttons = []
        labels = {
            "photo":"🖼 Foto",
            "sticker":"😊 Stiker",
            "video":"🎥 Video",
            "video_note":"🎬 Video Note",
            "audio":"🎵 Audio",
            "voice":"🎤 Voice",
            "document":"📄 Dokumen",
            "gif":"🎞 GIF",
            "contact":"👤 Kontak",
            "location":"📍 Lokasi",
        }
        for field in media_fields:
            idx = cols.index(field)
            val = settings[idx]
            buttons.append([InlineKeyboardButton(f"{labels[field]} {'✅' if val==1 else '❌'}", callback_data=f"personal_toggle:{field}:{owner_id}")])
        buttons.append([InlineKeyboardButton("⬅️ Kembali", callback_data="personal_settings")])
        await query.edit_message_text(text="🖼 <b>Pengaturan Media</b>\n\nAtur media apa saja yang boleh dikirim ke tautan pribadi Anda.", reply_markup=InlineKeyboardMarkup(buttons), parse_mode="HTML")
        return

    # Personal Features Menu
    if data == "personal_features":
        settings = await get_personal_settings(owner_id)
        if not settings:
            await query.edit_message_text(text="⚠️ Pengaturan personal tidak ditemukan.", parse_mode="HTML")
            return
        cols = ["owner_id","privacy","web_preview","formatting","photo","sticker","video","video_note","audio","voice","document","gif","contact","location"]
        def status(field):
            idx = cols.index(field)
            return "✅" if settings[idx]==1 else "❌"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"🔒 Privasi {status('privacy')}", callback_data=f"personal_toggle:privacy:{owner_id}"), InlineKeyboardButton(f"🌐 Pratinjau Web {status('web_preview')}", callback_data=f"personal_toggle:web_preview:{owner_id}")],
            [InlineKeyboardButton(f"📝 Pemformatan {status('formatting')}", callback_data=f"personal_toggle:formatting:{owner_id}"), InlineKeyboardButton("👥 Siapa yang dapat mengirim pesan", callback_data="personal_who_can_send")],
            [InlineKeyboardButton("⬅️ Kembali", callback_data="personal_settings")],
        ])
        await query.edit_message_text(text="✨ <b>Pengaturan Fitur</b>\n\nAtur fitur tautan pribadi Anda.", reply_markup=keyboard, parse_mode="HTML")
        return

    # Toggle personal settings (media/features)
    if data.startswith("personal_toggle:"):
        try:
            _, rest = data.split("personal_toggle:",1)
            field, oid = rest.split(":",1)
            owner = int(oid)
        except Exception:
            await query.answer("Invalid setting")
            return
        settings = await get_personal_settings(owner)
        if not settings:
            await query.answer("Settings not found")
            return
        cols = ["owner_id","privacy","web_preview","formatting","photo","sticker","video","video_note","audio","voice","document","gif","contact","location"]
        if field not in cols:
            await query.answer("Unknown field")
            return
        idx = cols.index(field)
        cur_val = settings[idx]
        new_val = 0 if cur_val==1 else 1
        await update_personal_setting(owner, field, new_val)
        # Refresh appropriate menu
        if field in {"photo","sticker","video","video_note","audio","voice","document","gif","contact","location"}:
            fake = update
            fake.callback_query.data = "personal_media"
            await handle_personal_link_callback(fake, context)
            return
        else:
            fake = update
            fake.callback_query.data = "personal_features"
            await handle_personal_link_callback(fake, context)
            return

    # Personal 'who can send' placeholder
    if data == "personal_who_can_send":
        text = "👥 Fitur ini akan tersedia pada pembaruan berikutnya."
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali", callback_data="personal_features")]])
        await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="HTML")
        return

    # Fallback
    await query.edit_message_text(text="🚧 Menu ini masih dalam tahap pengembangan.", parse_mode="HTML")


# handler for plain text inputs when awaiting actions (keeps create link flow only)
async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return
    uid = user.id
    text_content = update.message.text.strip()

    # create new link flow
    if context.user_data.get('awaiting_link_name'):
        name = text_content
        created_at = datetime.utcnow().isoformat()
        link_id, code = await create_link(uid, name, created_at)
        bot_username = context.bot.username or 'your_bot'
        link = f"https://t.me/{bot_username}?start={code}"
        text = f"✅ Tautan berhasil dibuat.\n\nNama:\n{name}\n\nTautan:\n{link}\n\nTautan tersebut dapat dibagikan ke Telegram, Instagram, TikTok, maupun media sosial lainnya."
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⚙️ Pengaturan", callback_data=f"link_settings:{link_id}"), InlineKeyboardButton("🗑 Cabut Tautan", callback_data=f"link_delete:{link_id}")],
            [InlineKeyboardButton("📤 Bagikan", callback_data=f"link_share:{link_id}")],
            [InlineKeyboardButton("⬅️ Kembali", callback_data="manage_links")]
        ])
        # edit original bot message
        menu = context.user_data.get('menu_message')
        if menu:
            chat_id, message_id = menu
            await context.bot.edit_message_text(text=text, chat_id=chat_id, message_id=message_id, reply_markup=keyboard, parse_mode='HTML', disable_web_page_preview=True)
        else:
            await update.message.reply_html(text)
        # clear flag
        context.user_data.pop('awaiting_link_name', None)
        return

    # other awaiting actions are part of link management; preserve previous minimal handling
    action = context.user_data.get('awaiting_action')
    if action:
        act, target = action
        value = text_content
        if act == 'change_name':
            await update_link_name(target, value)
            confirmation = "✅ Nama tautan berhasil diubah."
            menu = context.user_data.get('menu_message')
            if menu:
                chat_id, message_id = menu
                kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali", callback_data=f"link_settings:{target}")]])
                await context.bot.edit_message_text(text=confirmation, chat_id=chat_id, message_id=message_id, reply_markup=kb, parse_mode='HTML')
        elif act == 'adjust_slug':
            slug = ''.join(ch for ch in value if ch.isalnum() or ch in "-_")
            try:
                import aiosqlite
                from config import DATABASE_PATH
                async with aiosqlite.connect(DATABASE_PATH) as db:
                    await db.execute("UPDATE links SET slug = ? WHERE id = ?", (slug, target))
                    await db.commit()
                confirmation = "✅ Alamat tautan berhasil diperbarui."
            except Exception:
                confirmation = "⚠️ Gagal memperbarui alamat. Coba slug lain."
            menu = context.user_data.get('menu_message')
            if menu:
                chat_id, message_id = menu
                kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali", callback_data=f"general:{target}")]])
                await context.bot.edit_message_text(text=confirmation, chat_id=chat_id, message_id=message_id, reply_markup=kb, parse_mode='HTML')
        elif act == 'change_start_text':
            import aiosqlite
            from config import DATABASE_PATH
            async with aiosqlite.connect(DATABASE_PATH) as db:
                await db.execute("UPDATE links SET start_text = ? WHERE id = ?", (value, target))
                await db.commit()
            confirmation = "✅ Teks pembuka berhasil diperbarui."
            menu = context.user_data.get('menu_message')
            if menu:
                chat_id, message_id = menu
                kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali", callback_data=f"general:{target}")]])
                await context.bot.edit_message_text(text=confirmation, chat_id=chat_id, message_id=message_id, reply_markup=kb, parse_mode='HTML')
        elif act == 'change_end_text':
            import aiosqlite
            from config import DATABASE_PATH
            async with aiosqlite.connect(DATABASE_PATH) as db:
                await db.execute("UPDATE links SET end_text = ? WHERE id = ?", (value, target))
                await db.commit()
            confirmation = "✅ Teks penutup berhasil diperbarui."
            menu = context.user_data.get('menu_message')
            if menu:
                chat_id, message_id = menu
                kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali", callback_data=f"general:{target}")]])
                await context.bot.edit_message_text(text=confirmation, chat_id=chat_id, message_id=message_id, reply_markup=kb, parse_mode='HTML')
        # clear awaiting flag
        context.user_data.pop('awaiting_action', None)
        return

    # otherwise ignore
    return
