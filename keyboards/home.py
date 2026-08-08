from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def home_keyboard():
    keyboard = [
        [InlineKeyboardButton("🗂️ Pengelolaan Tautan", callback_data="manage_links"),
         InlineKeyboardButton("🔗 Tautan Pribadi Saya", callback_data="my_link")],
        [InlineKeyboardButton("📊 Statistik", callback_data="stats"),
         InlineKeyboardButton("🎨 Tema Bot", callback_data="theme_menu")],
        [InlineKeyboardButton("💡 Bantuan", callback_data="help"),
         InlineKeyboardButton("⚙️ Pengaturan", callback_data="settings")],
    ]
    return InlineKeyboardMarkup(keyboard)


def back_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali", callback_data="back_to_home")]])
