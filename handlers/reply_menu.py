from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from keyboards.home import inline_home_keyboard, main_reply_keyboard
from database import get_owner_by_code, get_user
from handlers.settings import stats_menu

async def reply_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle ReplyKeyboard main menu presses (text messages with menu labels)."""
    msg = update.message
    if not msg or not msg.text:
        return
    text = msg.text.strip()
    user_id = msg.from_user.id

    # Map labels to actions: send a message with an inline keyboard for the submenu
    if text == "🔗 Pengelolaan Tautan":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Buat Tautan", callback_data="manage_create")],
            [InlineKeyboardButton("📋 Daftar Tautan", callback_data="manage_list")],
            [InlineKeyboardButton("⬅️ Kembali", callback_data="back_to_home")],
        ])
        await context.bot.send_message(chat_id=user_id, text="🗂️ <b>Pengelolaan Tautan</b>\n\nKelola tautan anonimmu di sini.", reply_markup=keyboard, parse_mode="HTML")
        return

    if text == "👤 Tautan Pribadi":
        # show inline button that triggers existing my_link callback
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔗 Lihat Tautan Saya", callback_data="my_link")], [InlineKeyboardButton("⬅️ Kembali", callback_data="back_to_home")]])
        await context.bot.send_message(chat_id=user_id, text="🔗 <b>Tautan Pribadi</b>\n\nKelola tautan pribadi Anda.", reply_markup=keyboard, parse_mode="HTML")
        return

    if text == "📊 Statistik":
        # send a small loading message and call stats_menu via constructing a fake callback-like flow by sending inline keyboard that triggers stats
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Lihat Statistik", callback_data="stats")], [InlineKeyboardButton("⬅️ Kembali", callback_data="back_to_home")]])
        await context.bot.send_message(chat_id=user_id, text="📊 <b>Statistik Akun</b>\n\nTekan tombol untuk melihat statistik terkini.", reply_markup=keyboard, parse_mode="HTML")
        return

    if text == "🎨 Tema Bot":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🌌 Dark", callback_data="theme_select:dark")],
            [InlineKeyboardButton("💙 Ocean", callback_data="theme_select:ocean")],
            [InlineKeyboardButton("💜 Purple", callback_data="theme_select:purple")],
            [InlineKeyboardButton("🟢 Emerald", callback_data="theme_select:emerald")],
            [InlineKeyboardButton("🩶 Minimal", callback_data="theme_select:minimal")],
            [InlineKeyboardButton("⬅️ Kembali", callback_data="back_to_home")],
        ])
        await context.bot.send_message(chat_id=user_id, text="🎨 <b>Tema Bot</b>\n\nPilih tampilan favorit Anda.", reply_markup=keyboard, parse_mode="HTML")
        return

    if text == "💬 Bantuan":
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("❓ Cara Pakai", callback_data="help_usage")],[InlineKeyboardButton("⬅️ Kembali", callback_data="back_to_home")]])
        await context.bot.send_message(chat_id=user_id, text="💡 <b>Bantuan</b>\n\nPilih topik bantuan atau ketik pertanyaanmu.", reply_markup=keyboard, parse_mode="HTML")
        return

    if text == "⚙️ Pengaturan":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🛡️ Anti Spam", callback_data="anti_spam")],
            [InlineKeyboardButton("☣️ Filter Kata Kasar", callback_data="filter_badwords")],
            [InlineKeyboardButton("🎭 Personalisasi", callback_data="personalization")],
            [InlineKeyboardButton("⬅️ Kembali", callback_data="back_to_home")],
        ])
        await context.bot.send_message(chat_id=user_id, text="⚙️ <b>Pengaturan</b>\n\nSesuaikan pengalaman menggunakan bot.", reply_markup=keyboard, parse_mode="HTML")
        return

    # If message doesn't match menu labels, do nothing here (allow other handlers to process)
    return
