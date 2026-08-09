import os

# Read config values from environment variables if available
BOT_TOKEN = os.environ.get("BOT_TOKEN")
DATABASE_PATH = os.environ.get("DATABASE_PATH", "data/db.sqlite3")

# ADMIN_ID can be a single int or comma-separated list in env
_admin_raw = os.environ.get("ADMIN_ID", "")
if _admin_raw:
    try:
        if "," in _admin_raw:
            ADMIN_ID = [int(x.strip()) for x in _admin_raw.split(",") if x.strip()]
        else:
            ADMIN_ID = int(_admin_raw)
    except Exception:
        ADMIN_ID = _admin_raw
else:
    ADMIN_ID = None
