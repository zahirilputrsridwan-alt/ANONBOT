from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def admin_user_keyboard(user_id: int):
    kb = [
        [InlineKeyboardButton("⭐ Jadikan Premium", callback_data=f"admin:make_premium:{user_id}"),
         InlineKeyboardButton("⬇️ Turunkan ke Free", callback_data=f"admin:remove_premium:{user_id}")],
        [InlineKeyboardButton("🚫 Ban User", callback_data=f"admin:ban:{user_id}"),
         InlineKeyboardButton("✅ Unban User", callback_data=f"admin:unban:{user_id}")],
        [InlineKeyboardButton("⬅️ Kembali", callback_data="admin:manage_users")],
    ]
    return InlineKeyboardMarkup(kb)


def admin_premium_durations_keyboard(user_id: int):
    kb = [
        [InlineKeyboardButton("⭐ 7 Hari", callback_data=f"admin:make_premium_set:{user_id}:7")],
        [InlineKeyboardButton("⭐ 30 Hari", callback_data=f"admin:make_premium_set:{user_id}:30")],
        [InlineKeyboardButton("⭐ 90 Hari", callback_data=f"admin:make_premium_set:{user_id}:90")],
        [InlineKeyboardButton("⭐ 180 Hari", callback_data=f"admin:make_premium_set:{user_id}:180")],
        [InlineKeyboardButton("⭐ 365 Hari", callback_data=f"admin:make_premium_set:{user_id}:365")],
        [InlineKeyboardButton("♾️ Permanen", callback_data=f"admin:make_premium_set:{user_id}:permanent")],
        [InlineKeyboardButton("❌ Batal", callback_data="admin:manage_users")],
    ]
    return InlineKeyboardMarkup(kb)
