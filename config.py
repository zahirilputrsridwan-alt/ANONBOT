import os
from dotenv import load_dotenv

# Load .env if present (helps local testing). In Pterodactyl env vars override .env.
load_dotenv()

# Read config values from environment variables if available
BOT_TOKEN = os.environ.get("BOT_TOKEN")
DATABASE_PATH = os.environ.get("DATABASE_PATH", "data/db.sqlite3")

# ADMIN_ID can be a single int or comma-separated list in env
# Accept OWNER_ID as fallback to be compatible with other panels that use OWNER_ID.
_admin_raw = os.getenv("ADMIN_ID") or os.getenv("OWNER_ID") or ""
if _admin_raw:
    try:
        if "," in _admin_raw:
            ADMIN_ID = [int(x.strip()) for x in _admin_raw.split(",") if x.strip()]
        else:
            ADMIN_ID = int(_admin_raw)
    except Exception:
        # if parsing fails, keep raw value (string) — handlers should handle this case
        ADMIN_ID = _admin_raw
else:
    ADMIN_ID = None
