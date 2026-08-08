import asyncio
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from config import BOT_TOKEN
from database import init_db
from handlers.start import start
from handlers.callbacks import callback_handler
from handlers.links import handle_text_input

async def main():
    logging.basicConfig(level=logging.INFO)

    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set. Export BOT_TOKEN env var.")

    # Initialize database
    await init_db()

    # Build application
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback_handler))
    # catch plain text messages for flows (e.g., entering link name)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))

    logging.info("Bot started")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
