from telegram import Update
from telegram.ext import ContextTypes
from keyboards.home import home_keyboard
from handlers.links import (
    handle_manage_links_callback,
    handle_personal_link_callback,
    handle_sendpage_callback,
    handle_send_type_choice,
    handle_send_cancel,
    handle_send_again,
    handle_open_message_callback,
    handle_reply_callback,
)

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    await query.answer()
    data = query.data or ""

    # Route to link management handler if prefix matches
    if data.startswith("manage_") or data.startswith("add_") or data.startswith("list_") or data.startswith("link_") or data.startswith("general:") or data.startswith("toggle_") or data.startswith("setting_") or data.startswith("change_") or data.startswith("adjust_"):
        await handle_manage_links_callback(update, context)
        return

    # Personal link handling
    if data == "my_link" or data.startswith("personal_"):
        await handle_personal_link_callback(update, context)
        return

    # Inline sendpage flows
    if data.startswith("sendpage:"):
        await handle_sendpage_callback(update, context)
        return

    if data.startswith(("send_text:", "send_photo:", "send_video:")):
        await handle_send_type_choice(update, context)
        return

    if data == "send_cancel":
        await handle_send_cancel(update, context)
        return

    if data.startswith(("send_again:", "send_photo_again:", "send_video_again:")):
        await handle_send_again(update, context)
        return

    # Open message / reply flows
    if data.startswith("open_msg:"):
        await handle_open_message_callback(update, context)
        return

    if data.startswith("reply:"):
        await handle_reply_callback(update, context)
        return

    # reply confirmation actions (send_again from confirmation buttons handled above)

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
    await query.edit_message_text(text=text, parse_mode="HTML")
