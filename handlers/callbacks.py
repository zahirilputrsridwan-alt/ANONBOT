from telegram import Update
from telegram.ext import ContextTypes
from keyboards.home import home_keyboard
from handlers.links import handle_manage_links_callback

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    await query.answer()
    data = query.data or ""

    # Route to link management handler if prefix matches
    if data.startswith("manage_") or data.startswith("add_") or data.startswith("list_") or data.startswith("link_") or data.startswith("general_") or data.startswith("toggle_") or data.startswith("setting_"):
        await handle_manage_links_callback(update, context)
        return

    if data == "back_to_home":
        text = (
            "Wih, halo bro! Selamat datang di markas rahasia lu. Siapin mental, bentar lagi bakal banyak spill rahasia masuk nih wkwk 🤫🔥\n\n"
            "Gunakan tombol di bawah untuk melihat menu."
        )
        keyboard = home_keyboard()
        await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="HTML", disable_web_page_preview=True)
        return

    # default placeholder for other callbacks
    text = "🚧 Menu ini masih dalam tahap pengembangan."
    keyboard = [[{"text":"⬅️ Kembali","callback_data":"back_to_home"}]]
    await query.edit_message_text(text=text, reply_markup=None, parse_mode="HTML")
