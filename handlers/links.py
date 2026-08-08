import secrets
import random
from datetime import datetime
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from telegram.ext import ContextTypes
from database import (
    create_link, get_links_by_owner, get_link_by_id, get_link_settings,
    toggle_link_status, update_setting, count_messages_for_link, update_link_name,
    get_user, get_personal_settings, update_personal_setting, count_messages_for_user,
    get_owner_by_code, add_message, get_user_by_code
)

# Random messages list (easy to modify)
random_messages = [
    "Wah mau nyoba nge-spill nih ye? Ketik apa aja yang ada di kepala lu sekarang, gak bakal ketahuan siapa yang kirim kok. Santai bro! 🤫☕️",
    "Lagi gabut ya? Sok lah curhat atau kirim sesuatu yang random ke sini. Mumpung aman gak ketahuan bosnya wkwk. 👇🔥",
    "Jujur aja, lagi pendam rasa atau mau ngerjain dia? Bebas ketik apa aja di sini, dijamin aman tanpa jejak! 🥷✨",
    "Seru banget tumben mau ngirim rahasia ke dia. Coba ketik unek-unek lu yang paling jujur di bawah ini, tenang aja identitas lu aman 100% kok! 👇✨",
]


def pick_random_message(context: ContextTypes.DEFAULT_TYPE) -> str:
    """Pick a random message from random_messages trying to avoid immediate repeat for this user."""
    if not random_messages:
        return ""
    last = context.user_data.get('last_random_message')
    if len(random_messages) == 1:
        chosen = random_messages[0]
        context.user_data['last_random_message'] = chosen
        return chosen

    # try a few times to get a different one
    for _ in range(10):
        chosen = random.choice(random_messages)
        if chosen != last:
            context.user_data['last_random_message'] = chosen
            return chosen
    # fallback to chosen even if same
    context.user_data['last_random_message'] = chosen
    return chosen


# ---------------------------
# Inline Query (share result)
# ---------------------------
async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Respond to inline queries. The inline query 'query' will be pre-filled by switch_inline_query_current_chat
    with the owner's unique_code (or contain it). We respond with one InlineQueryResultArticle that,
    when chosen, posts a message with two buttons: 'Kirim Pesan Anonim Lu' and 'Kirim Hadiah Anonim Lu'.
    """
    inline_query = update.inline_query
    q = (inline_query.query or "").strip()
    results = []

    # If query empty, return no results
    if not q:
        await inline_query.answer(results, cache_time=1)
        return

    # find owner by code (do NOT reveal owner identity)
    owner_id = await get_owner_by_code(q)
    if not owner_id:
        await inline_query.answer(results, cache_time=1)
        return

    # Build an article result that when selected posts a message with buttons
    title = "Bagikan Tautan Anonim"
    message_text = "📣 Bagikan tautan anonim ini — pilih aksi di bawah:"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💌 Kirim Pesan Anonim Lu", callback_data=f"sendpage:message:{q}")],
        [InlineKeyboardButton("🎁 Kirim Hadiah Anonim Lu", callback_data=f"sendpage:gift:{q}")],
    ])

    input_content = InputTextMessageContent(message_text, parse_mode="HTML")
    result = InlineQueryResultArticle(
        id=secrets.token_hex(8),
        title=title,
        input_message_content=input_content,
        description="Kirim pesan anonim ke pemilik tautan (identitas tersamarkan).",
        reply_markup=keyboard,
    )

    results.append(result)
    await inline_query.answer(results, cache_time=1, is_personal=True)


# ---------------------------
# Callback flows for inline result buttons and send pages
# ---------------------------
async def handle_sendpage_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle callback_data starting with 'sendpage:' which originates from the inline result message.
    Expected format: sendpage:<type>:<unique_code>
    type: message | gift
    """
    query = update.callback_query
    data = query.data or ""
    await query.answer()

    parts = data.split(":", 2)
    if len(parts) < 3:
        await query.edit_message_text("Terjadi kesalahan.", parse_mode="HTML")
        return

    _, kind, code = parts
    owner_id = await get_owner_by_code(code)
    if not owner_id:
        await query.edit_message_text("Tautan tujuan tidak ditemukan.", parse_mode="HTML")
        return

    # prepare a random tracking token shown to sender (pesan_acak)
    token = secrets.token_hex(3)
    # pick a random prompt message and store it to use in subsequent pages
    rand_msg = pick_random_message(context)
    context.user_data['sending_to'] = {"owner_id": owner_id, "code": code, "token": token}
    context.user_data['random_message_current'] = rand_msg

    # Compose "Halaman Kirim Pesan Anonim"
    text = f"💌 <b>Kirim Pesan Anonim</b>\n\n#{token}\n\n{rand_msg}\n\nPilih jenis pesan yang ingin dikirim:"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Pesan Teks", callback_data=f"send_text:{code}:{token}" )],
        [InlineKeyboardButton("🖼 Kirim Foto", callback_data=f"send_photo:{code}:{token}" )],
        [InlineKeyboardButton("🎥 Kirim Video", callback_data=f"send_video:{code}:{token}" )],
        [InlineKeyboardButton("❌ Batal", callback_data="send_cancel")],
    ])
    await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="HTML")


async def handle_send_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="❌ Pengiriman dibatalkan.", parse_mode="HTML")


# When sender chooses type, set awaiting state and prompt
async def handle_send_type_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data or ""
    await query.answer()
    # data format: send_text:<code>:<token>  or send_photo:... or send_video:...
    try:
        kind, code, token = data.split(":", 2)
    except Exception:
        await query.edit_message_text("Terjadi kesalahan.", parse_mode="HTML")
        return

    kind_key = kind.replace("send_", "")

    # Save awaiting state for this user
    context.user_data['awaiting_send'] = {"kind": kind_key, "code": code, "token": token, "menu_message": (query.message.chat.id, query.message.message_id)}

    # Use existing random message if set, otherwise pick a new one
    rand_msg = context.user_data.get('random_message_current') or pick_random_message(context)
    # ensure random_message_current is set for follow-ups
    context.user_data['random_message_current'] = rand_msg

    display_token = f"#{token}"
    if kind == "send_text":
        text = f"💬 <b>Pesan Teks</b>\n\n{rand_msg}"
    elif kind == "send_photo":
        text = f"🖼 <b>Kirim Foto</b>\n\n{rand_msg}\n\nKirim foto sekarang (dengan caption jika ingin)."
    elif kind == "send_video":
        text = f"🎥 <b>Kirim Video</b>\n\n{rand_msg}\n\nKirim video sekarang (dengan caption jika ingin)."
    else:
        text = "Terjadi kesalahan."

    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Batal", callback_data="send_cancel")]])
    await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="HTML")


# ---------------------------
# Handlers for incoming content (sender -> send anonymous)
# ---------------------------
async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return

    awaiting = context.user_data.get('awaiting_send')
    if not awaiting:
        return

    if awaiting.get("kind") != "text":
        return

    content = update.message.text.strip()
    owner_id = await get_owner_by_code(awaiting['code'])
    if not owner_id:
        await update.message.reply_text("Tautan tujuan tidak ditemukan.")
        context.user_data.pop('awaiting_send', None)
        return

    # Save message to DB
    await add_message(owner_id=owner_id, link_code=awaiting['code'], message_type="text", content=content, file_id=None)

    # Send anonymous message to owner (as bot); DO NOT include sender identity
    anonymous_text = f"✉️ <b>Pesan Anonim Masuk</b>\n\n{content}"
    await context.bot.send_message(chat_id=owner_id, text=anonymous_text, parse_mode="HTML")

    # Send confirmation back to sender (edit the menu message if available, else reply)
    token = awaiting.get("token")
    confirm_text = f"✅ <b>Pesan berhasil dikirim.</b>\n\n#{token}"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💌 Kirim Lagi", callback_data=f"send_again:{awaiting['code']}")],
        [InlineKeyboardButton("🏠 Menu Utama", callback_data="back_to_home")],
    ])
    menu = awaiting.get("menu_message")
    if menu:
        chat_id, message_id = menu
        await context.bot.edit_message_text(text=confirm_text, chat_id=chat_id, message_id=message_id, reply_markup=keyboard, parse_mode="HTML")
    else:
        await update.message.reply_html(confirm_text, reply_markup=keyboard)

    # clear awaiting
    context.user_data.pop('awaiting_send', None)


async def handle_photo_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return
    awaiting = context.user_data.get('awaiting_send')
    if not awaiting or awaiting.get('kind') != 'photo':
        return

    photo = update.message.photo[-1]
    file_id = photo.file_id
    caption = (update.message.caption or "").strip()
    owner_id = await get_owner_by_code(awaiting['code'])
    if not owner_id:
        await update.message.reply_text("Tautan tujuan tidak ditemukan.")
        context.user_data.pop('awaiting_send', None)
        return

    # Save to DB (store file_id)
    await add_message(owner_id=owner_id, link_code=awaiting['code'], message_type="photo", content=caption, file_id=file_id)

    # Send anonymous photo to owner (bot sends file_id)
    await context.bot.send_photo(chat_id=owner_id, photo=file_id, caption=f"✉️ <b>Foto Anonim</b>\n\n{caption}", parse_mode="HTML")

    # confirmation to sender
    token = awaiting.get("token")
    confirm_text = f"✅ <b>Foto berhasil dikirim.</b>\n\n#{token}"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🖼 Kirim Foto Lagi", callback_data=f"send_photo_again:{awaiting['code']}" )],
        [InlineKeyboardButton("🏠 Menu Utama", callback_data="back_to_home")],
    ])
    menu = awaiting.get("menu_message")
    if menu:
        chat_id, message_id = menu
        await context.bot.edit_message_text(text=confirm_text, chat_id=chat_id, message_id=message_id, reply_markup=keyboard, parse_mode="HTML")
    else:
        await update.message.reply_html(confirm_text, reply_markup=keyboard)

    context.user_data.pop('awaiting_send', None)


async def handle_video_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return
    awaiting = context.user_data.get('awaiting_send')
    if not awaiting or awaiting.get('kind') != 'video':
        return

    video = update.message.video
    file_id = video.file_id
    caption = (update.message.caption or "").strip()
    owner_id = await get_owner_by_code(awaiting['code'])
    if not owner_id:
        await update.message.reply_text("Tautan tujuan tidak ditemukan.")
        context.user_data.pop('awaiting_send', None)
        return

    # Save to DB
    await add_message(owner_id=owner_id, link_code=awaiting['code'], message_type="video", content=caption, file_id=file_id)

    # Send anonymous video to owner
    await context.bot.send_video(chat_id=owner_id, video=file_id, caption=f"✉️ <b>Video Anonim</b>\n\n{caption}", parse_mode="HTML")

    # confirmation to sender
    token = awaiting.get("token")
    confirm_text = f"✅ <b>Video berhasil dikirim.</b>\n\n#{token}"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎥 Kirim Video Lagi", callback_data=f"send_video_again:{awaiting['code']}" )],
        [InlineKeyboardButton("🏠 Menu Utama", callback_data="back_to_home")],
    ])
    menu = awaiting.get('menu_message')
    if menu:
        chat_id, message_id = menu
        await context.bot.edit_message_text(text=confirm_text, chat_id=chat_id, message_id=message_id, reply_markup=keyboard, parse_mode="HTML")
    else:
        await update.message.reply_html(confirm_text, reply_markup=keyboard)

    context.user_data.pop('awaiting_send', None)


# Small helper to start "send again" flows triggered by confirm buttons
async def handle_send_again(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data or ""
    # formats: send_again:<code>, send_photo_again:<code>, send_video_again:<code>
    parts = data.split(":", 1)
    if len(parts) != 2:
        await query.edit_message_text("Terjadi kesalahan.", parse_mode="HTML")
        return
    cmd, code = parts
    if cmd == "send_again":
        token = secrets.token_hex(3)
        owner_id = await get_owner_by_code(code)
        if not owner_id:
            await query.edit_message_text("Tautan tujuan tidak ditemukan.", parse_mode="HTML")
            return
        context.user_data['sending_to'] = {"owner_id": owner_id, "code": code, "token": token}
        # pick a fresh random message for this retry
        rand_msg = pick_random_message(context)
        context.user_data['random_message_current'] = rand_msg
        text = f"💌 <b>Kirim Pesan Anonim</b>\n\n#{token}\n\n{rand_msg}\n\nPilih jenis pesan yang ingin dikirim:"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💬 Pesan Teks", callback_data=f"send_text:{code}:{token}" )],
            [InlineKeyboardButton("🖼 Kirim Foto", callback_data=f"send_photo:{code}:{token}" )],
            [InlineKeyboardButton("🎥 Kirim Video", callback_data=f"send_video:{code}:{token}" )],
            [InlineKeyboardButton("❌ Batal", callback_data="send_cancel")],
        ])
        await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await query.edit_message_text("Perintah tidak dikenali.", parse_mode="HTML")
