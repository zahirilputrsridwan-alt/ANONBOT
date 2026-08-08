import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
DATABASE_PATH = os.environ.get("DATABASE_PATH", "data/database.db")
