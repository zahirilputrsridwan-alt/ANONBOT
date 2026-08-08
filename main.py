import asyncio
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from config import BOT_TOKEN
from database import init_db
from handlers.start import start
from handlers.callbacks import callback_handler

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

    logging.info("Bot started")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
