from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Reusable keyboards for links menus

def manage_links_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Tambahkan Tautan Baru", callback_data="add_new_link")],
        [InlineKeyboardButton("📂 Daftar Tautan", callback_data="list_links")],
        [InlineKeyboardButton("⬅️ Kembali", callback_data="back_to_home")],
    ])


def link_created_keyboard(link_id: int):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚙️ Pengaturan", callback_data=f"link_settings:{link_id}"), InlineKeyboardButton("🗑 Cabut Tautan", callback_data=f"link_delete:{link_id}")],
        [InlineKeyboardButton("📤 Bagikan", callback_data=f"link_share:{link_id}"), InlineKeyboardButton("⬅️ Kembali", callback_data="manage_links")]
    ])
