import asyncio
import logging
import os
import html
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from database import init_db

# Import admin and reply handlers (they should exist in handlers/)
try:
    from handlers.admin_premium import admin_user_command, admin_callback_router
except Exception:
    # fallback stubs if file not present
    async def admin_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Admin handler belum tersedia.")

    async def admin_callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        if query:
            await query.answer()
            await query.edit_message_text("Admin router belum tersedia.")

try:
    from handlers.reply_menu import reply_menu_handler
except Exception:
    async def reply_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Minimal fallback: echo the received text
        if update.message and update.message.text:
            await update.message.reply_text(f"Anda memilih: {update.message.text}")

# Import start handler
try:
    from handlers.start import start_handler
except Exception:
    async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Halo. /start handler belum tersedia.")

# Generic callback handler that routes admin:* callbacks to admin handler
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    await query.answer()
    data = (query.data or "").strip()

    # Route admin callbacks to the admin router if available
    if data.startswith("admin:"):
        try:
            await admin_callback_router(update, context)
            return
        except Exception as e:
            logging.exception("Error in admin_callback_router: %s", e)
            try:
                await query.edit_message_text("Terjadi kesalahan pada admin handler.")
            except Exception:
                pass
            return

    # For other callbacks, provide a simple acknowledgment so buttons are not silent
    try:
        await query.edit_message_text(text=f"✔️ Tombol diterima: <code>{html.escape(data)}</code>", parse_mode="HTML")
    except Exception:
        try:
            await query.message.reply_text(f"✔️ Tombol diterima: {data}")
        except Exception:
            logging.exception("Gagal mengirim acknowledgment untuk callback data: %s", data)

# Text handler that delegates to reply_menu_handler (handles ReplyKeyboard main menu labels)
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Ensure we have message text
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip()
    # If reply_menu_handler exists, call it to show inline submenus
    try:
        await reply_menu_handler(update, context)
    except Exception as e:
        logging.exception("Error in reply_menu_handler: %s", e)
        # fallback simple behavior for known labels
        labels = {
            "👤 Tautan Pribadi": "🔗 Membuka Tautan Pribadi...",
            "🔗 Pengelolaan Tautan": "🗂️ Membuka Pengelolaan Tautan...",
            "📊 Statistik": "📊 Membuka Statistik...",
            "🎨 Tema Bot": "🎨 Membuka Tema Bot...",
            "⚙️ Pengaturan": "⚙️ Membuka Pengaturan...",
            "❓ Bantuan": "❓ Membuka Bantuan...",
        }
        resp = labels.get(text, None)
        if resp:
            await update.message.reply_text(resp)
        else:
            # generic echo for other messages
            await update.message.reply_text("Pesan diterima.")


async def setup():
    # Initialize DB and migrations
    await init_db()


async def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Ensure DATABASE and other init steps
    await setup()

    token = os.environ.get("BOT_TOKEN")
    if not token:
        logger.error("BOT_TOKEN environment variable not set. Exiting.")
        return

    app = ApplicationBuilder().token(token).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("admin_user", admin_user_command))

    # Message handler for reply keyboard main menu (and general text)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Keep a single callback query handler and route inside it
    app.add_handler(CallbackQueryHandler(callback_handler))

    # Do NOT register handlers that previously caused errors (removed as requested)
    # e.g. InlineQueryHandler(inline_query_handler), handle_text_input, handle_manage_links_callback, etc.

    # Start polling (this will run until process is stopped)
    logger.info("Starting bot polling...")
    await app.run_polling()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped")
