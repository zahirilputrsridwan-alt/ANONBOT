import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import (
    get_user, set_premium, remove_premium, get_account_info, get_user_limits, ban_user, unban_user, is_user_banned
)
from config import ADMIN_ID
import html
from keyboards.admin import admin_user_keyboard, admin_premium_durations_keyboard


def is_admin(user_id: int):
    # ADMIN_ID in config can be int or list
    if isinstance(ADMIN_ID, list):
        return user_id in ADMIN_ID
    return user_id == ADMIN_ID


async def admin_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("⛔ Anda tidak memiliki izin untuk menggunakan menu ini.")
        return
    # Expect argument: user_id
    args = context.args
    if not args:
        await update.message.reply_text("Gunakan: /admin_user <user_id>")
        return
    try:
        target_id = int(args[0])
    except ValueError:
        await update.message.reply_text("User ID tidak valid.")
        return
    await send_user_info(update, context, target_id)


async def send_user_info(update_or_query, context: ContextTypes.DEFAULT_TYPE, target_id: int):
    # update_or_query can be Update from command or CallbackQuery
    info = await get_account_info(target_id)
    user_row = await get_user(target_id)
    if not user_row:
        text = f"👤 Pengguna tidak ditemukan: <b>{target_id}</b>"
    else:
        name = html.escape(user_row[1] or user_row[0])
        join_date = user_row[3] or "-"
        acct = info['account_type']
        if acct == 'premium':
            if info['premium_expired'] is None:
                status = "💎 Premium Permanen"
                expires = "♾️"
            else:
                status = "💎 Premium"
                expires = html.escape(info['premium_expired'])
        else:
            status = "🆓 Free"
            expires = "-"
        limits = await get_user_limits(target_id)
        text = (
            f"👤 <b>Informasi Pengguna</b>\n\n"
            f"🆔 ID: <b>{target_id}</b>\n"
            f"👤 Nama: <b>{name}</b>\n"
            f"📅 Bergabung: <b>{html.escape(join_date)}</b>\n"
            f"⭐ Status: <b>{status}</b>\n"
            f"⏳ Berlaku sampai: <b>{expires}</b>\n\n"
            f"📝 Limit Pesan: <b>{limits['messages']}</b>\n"
            f"🖼️ Limit Foto: <b>{limits['photos']}</b>\n"
            f"🎥 Limit Video: <b>{limits['videos']}</b>\n"
            f"🔗 Tautan Tambahan: <b>{limits['links']}</b>\n"
        )
    kb = admin_user_keyboard(target_id)
    # If called from command Update
    if hasattr(update_or_query, 'message') and update_or_query.message:
        await update_or_query.message.reply_text(text, reply_markup=kb, parse_mode="HTML")
    else:
        # callback query
        query = update_or_query.callback_query
        await query.answer()
        await query.edit_message_text(text=text, reply_markup=kb, parse_mode="HTML")


async def admin_callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    if not is_admin(user.id):
        await query.edit_message_text("⛔ Anda tidak memiliki izin untuk menggunakan menu ini.")
        return
    data = query.data
    # callbacks: admin:make_premium:<user_id> , admin:make_premium_set:<user_id>:<days|permanent>
    # admin:remove_premium:<user_id>
    # admin:ban:<user_id>
    # admin:unban:<user_id>
    parts = data.split(":")
    if parts[0] != 'admin':
        return
    cmd = parts[1]
    if cmd == 'make_premium' and len(parts) == 3:
        target_id = int(parts[2])
        # show durations keyboard
        kb = admin_premium_durations_keyboard(target_id)
        await query.edit_message_text(f"⭐ Pilih durasi Premium untuk user <b>{target_id}</b>", reply_markup=kb, parse_mode="HTML")
        return
    if cmd == 'make_premium_set' and len(parts) == 4:
        target_id = int(parts[2])
        val = parts[3]
        if val == 'permanent':
            await set_premium(target_id, None, user.id)
            await query.edit_message_text(f"✅ User <b>{target_id}</b> telah dijadikan Premium Permanen.", parse_mode="HTML")
            return
        try:
            days = int(val)
        except ValueError:
            await query.edit_message_text("Pilihan durasi tidak valid.")
            return
        await set_premium(target_id, days, user.id)
        await query.edit_message_text(f"✅ User <b>{target_id}</b> dijadikan Premium selama <b>{days} hari</b>.", parse_mode="HTML")
        return
    if cmd == 'remove_premium' and len(parts) == 3:
        target_id = int(parts[2])
        await remove_premium(target_id)
        await query.edit_message_text(f"✅ Pengguna <b>{target_id}</b> berhasil dikembalikan ke akun Free.", parse_mode="HTML")
        return
    if cmd == 'ban' and len(parts) == 3:
        target_id = int(parts[2])
        await ban_user(target_id, reason=f"banned by admin {user.id}")
        await query.edit_message_text(f"🚫 User <b>{target_id}</b> diblokir.", parse_mode="HTML")
        return
    if cmd == 'unban' and len(parts) == 3:
        target_id = int(parts[2])
        await unban_user(target_id)
        await query.edit_message_text(f"✅ User <b>{target_id}</b> di-unban.", parse_mode="HTML")
        return
    if cmd == 'manage_users':
        # go back placeholder
        await query.edit_message_text("🔍 Panel Kelola User\n\nGunakan /admin_user <user_id> untuk mencari user.")
        return
