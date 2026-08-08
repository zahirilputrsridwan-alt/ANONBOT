from telegram import Update
from telegram.ext import ContextTypes
from keyboards.home import home_keyboard
from database import add_user_if_not_exists
from datetime import datetime

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return

    user_id = user.id
    first_name = user.first_name or ""
    username = user.username or ""
    join_date = datetime.utcnow().isoformat()

    # add user to database if not exists, returns unique_code
    unique_code = await add_user_if_not_exists(user_id, first_name, username, join_date)

    bot_username = context.bot.username or "your_bot"
    personal_link = f"https://t.me/{bot_username}?start={unique_code}"

    text = (
        "Wih, halo bro! Selamat datang di markas rahasia lu. Siapin mental, bentar lagi bakal banyak spill rahasia masuk nih wkwk 🤫🔥\n\n"
        f"🔗 Tautan Pribadi Anda\n{personal_link}\n\n"
        "Eh bro, lu dateng di waktu yang pas! Salin link lu, sebarin ke sosmed, terus tunggu spill rahasia masuk ☕️👀\n\n"
        "Asik, lu udah nyala nih bre! Siapin link lu, taruh di bio ig/tiktok, dan nikmati keseruan dibully secara misterius wkwk 💀✌️\n\n"
        "💬 Jika membutuhkan bantuan, buka menu Bantuan di bawah ye brooo....."
    )

    keyboard = home_keyboard()

    # reply with HTML parse mode and disable web page preview
    await update.message.reply_html(text=text, reply_markup=keyboard, disable_web_page_preview=True)
