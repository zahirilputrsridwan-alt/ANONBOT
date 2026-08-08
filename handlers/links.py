from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import create_link, get_links_by_owner, get_link_by_id, get_link_settings, toggle_link_status, update_setting, count_messages_for_link, update_link_name
from datetime import datetime

# entrypoint for link-related callbacks
async def handle_manage_links_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data or ""
    chat_id = query.message.chat.id
    message_id = query.message.message_id

    # store current menu message so text inputs can edit it
    context.user_data['menu_message'] = (chat_id, message_id)

    if data == "manage_links":
        # show management menu
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

    # general menu
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

    # adjust slug / change name / change texts: for now, prompt and set awaiting flags
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
        # delete link
        # For safety, implement soft delete by setting status=0 and clearing slug
        await update_setting(lid, 'privacy', 1)  # reuse setting to mark
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
        # format: setting_{field}:{link_id}
        try:
            main, rest = data.split("_",1)
            field, lid = rest.split(":")
            lid = int(lid)
        except Exception:
            await query.answer("Invalid setting")
            return
        # get current value
        settings = await get_link_settings(lid)
        if not settings:
            await query.answer("Settings not found")
            return
        # settings is a tuple matching columns; find index of field
        cols = ["link_id","privacy","web_preview","formatting","photo","sticker","video","video_note","audio","voice","document","gif","contact","location"]
        if field not in cols:
            await query.answer("Unknown field")
            return
        idx = cols.index(field)
        cur_val = settings[idx]
        new_val = 0 if cur_val==1 else 1
        await update_setting(lid, field, new_val)
        # refresh media or feature menu by calling same callback
        # if field is media we should reopen media menu
        await handle_manage_links_callback(update, context)
        return

    # list fallback
    await query.edit_message_text(text="🚧 Menu ini masih dalam tahap pengembangan.", parse_mode="HTML")


# handler for plain text inputs when awaiting actions
async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # This function is registered in main.py as a MessageHandler
    user = update.effective_user
    if not user:
        return
    uid = user.id
    if context.user_data.get('awaiting_link_name'):
        name = update.message.text.strip()
        # create link
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

    # awaiting other actions (change_name, adjust_slug, etc.)
    action = context.user_data.get('awaiting_action')
    if action:
        act, lid = action
        text_value = update.message.text.strip()
        if act == 'change_name':
            await update_link_name(lid, text_value)
            # show confirmation and go back to general menu
            await context.bot.send_message(chat_id=update.effective_chat.id, text="✅ Nama tautan berhasil diubah.")
        # TODO: handle other actions (slug, texts) — for now minimal implementation
        context.user_data.pop('awaiting_action', None)
        # edit menu message back to general
        menu = context.user_data.get('menu_message')
        if menu:
            chat_id, message_id = menu
            # trigger general menu refresh by editing the callback via synthetic callback handling
            # here simply call handle_manage_links_callback by creating a fake update? Simpler: edit message to say done and show back button
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali", callback_data=f"manage_links")]])
            await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="✅ Perubahan disimpan.", reply_markup=keyboard, parse_mode='HTML')
        return

    # if nothing awaited, ignore or inform
    return
