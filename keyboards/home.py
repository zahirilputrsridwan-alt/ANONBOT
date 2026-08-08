from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

# Inline keyboard used in submenus (kept for compatibility with existing inline flows)
def inline_home_keyboard():
    keyboard = [
        [InlineKeyboardButton("🗂️ Pengelolaan Tautan", callback_data="manage_links"),
         InlineKeyboardButton("🔗 Tautan Pribadi Saya", callback_data="my_link")],
        [InlineKeyboardButton("📊 Statistik", callback_data="stats"),
         InlineKeyboardButton("🎨 Tema Bot", callback_data="theme_menu")],
        [InlineKeyboardButton("💡 Bantuan", callback_data="help"),
         InlineKeyboardButton("⚙️ Pengaturan", callback_data="settings")],
    ]
    return InlineKeyboardMarkup(keyboard)


# Reply keyboard that appears as the main persistent menu
def main_reply_keyboard():
    keyboard = [
        ["🔗 Pengelolaan Tautan", "👤 Tautan Pribadi"],
        ["📊 Statistik", "🎨 Tema Bot"],
        ["💬 Bantuan", "⚙️ Pengaturan"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, is_persistent=True, input_field_placeholder="💬 Kirim pesan atau pilih menu...")


def back_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali", callback_data="back_to_home")]])
