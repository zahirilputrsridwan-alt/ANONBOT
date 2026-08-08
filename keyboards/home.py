from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def home_keyboard():
    keyboard = [
        [InlineKeyboardButton("🗂️ Pengelolaan Tautan", callback_data="manage_links"),
         InlineKeyboardButton("🔗 Tautan Pribadi Saya", callback_data="my_link")],
        [InlineKeyboardButton("💡 Bantuan", callback_data="help"),
         InlineKeyboardButton("🛡️ Tentang Kami", callback_data="about")],
        [InlineKeyboardButton("💎 Tingkatkan", callback_data="upgrade"),
         InlineKeyboardButton("🎁 Hadiah & Pesan", callback_data="gifts")],
    ]
    return InlineKeyboardMarkup(keyboard)


def back_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali", callback_data="back_to_home")]])
