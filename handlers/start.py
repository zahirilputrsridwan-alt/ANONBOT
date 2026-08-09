from telegram import Update
from telegram.ext import ContextTypes
from keyboards.home import main_reply_keyboard
from database import add_user_if_not_exists
import datetime

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    # Register user in DB if function exists
    try:
        code = await add_user_if_not_exists(user.id, user.first_name or "", user.username or "", datetime.datetime.utcnow().isoformat())
    except Exception:
        # ignore if DB helper not available
        code = None
    kb = main_reply_keyboard()
    text = "Halo! Selamat datang. Gunakan keyboard di bawah untuk navigasi utama."
    await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=kb)
