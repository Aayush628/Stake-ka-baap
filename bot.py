import os
import logging
import hashlib
import random
from PIL import Image, ImageDraw
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from datetime import datetime

# --- Constants ---
PASSKEY_BASIC = "AqWSedrFtgYHUjIkOlP"
PASSKEY_KING = "ZawEDxcftGvYUJnHy"
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# --- States ---
SELECT_PLAN, ENTER_PASSKEY, ENTER_CLIENT_SEED = range(3)

# --- Logging ---
logging.basicConfig(level=logging.INFO)

# --- Start Command ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name
    msg = f"👋 Hello {name}!\n\nChoose a prediction plan:"
    
    buttons = [
        [InlineKeyboardButton("💎 Mines Basic", callback_data="basic")],
        [InlineKeyboardButton("👑 Mines King", callback_data="king")]
    ]
    
    await update.message.reply_text(
        msg + "\n\n📋 *Plan Details:*\n\n"
        "💎 *Mines Basic* — Lifetime Access\n• 20 Sureshot signals per day\n\n"
        "👑 *Mines King* — Lifetime Access\n• 45 Sureshot signals per day\n\n"
        f"🔔 *Recommendation: {name}, Mines King will be a better choice for you!*",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown"
    )
    return SELECT_PLAN

# --- Plan Selection ---
async def plan_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    plan = query.data
    context.user_data['plan'] = plan

    await query.message.reply_text(
        "🔐 Please enter your *passkey* to continue.\n\n"
        "⚠️ If you don't have a passkey, contact Admin → @Stake_Mines_God",
        parse_mode="Markdown"
    )
    return ENTER_PASSKEY

# --- Passkey Handling ---
async def handle_passkey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()
    selected_plan = context.user_data.get('plan')

    if (selected_plan == "basic" and user_input == PASSKEY_BASIC) or \
       (selected_plan == "king" and user_input == PASSKEY_KING):
        await update.message.reply_text(
            "✅ Passkey verified!\n\nPlease enter your *Client Seed* to begin.",
            parse_mode="Markdown"
        )
        await update.message.reply_text(
            "⚠️ *Disclaimer:* Please play with only 3 mines.",
            parse_mode="Markdown"
        )
        return ENTER_CLIENT_SEED
    else:
        await update.message.reply_text(
            "❌ Invalid passkey. Please try again or contact @Stake_Mines_God."
        )
        return ENTER_PASSKEY

# --- Image Generator ---
def generate_prediction_image(safe_tiles):
    tile_size = 64
    grid_size = 5
    img = Image.new("RGB", (tile_size * grid_size, tile_size * grid_size), color=(20, 20, 30))
    draw = ImageDraw.Draw(img)

    for i in range(25):
        row, col = divmod(i, 5)
        x, y = col * tile_size, row * tile_size
        if i in safe_tiles:
            draw.ellipse([x+10, y+10, x+54, y+54], fill=(0, 255, 100))  # Green diamond
        else:
            draw.rectangle([x+8, y+8, x+56, y+56], fill=(50, 50, 60))

    return img

# --- Seed Handling ---
async def handle_client_seed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    seed = update.message.text.strip()
    hash_value = hashlib.sha256(seed.encode()).hexdigest()
    random.seed(hash_value)
    safe_tiles = random.sample(range(25), 5)

    img = generate_prediction_image(safe_tiles)
    bio = io.BytesIO()
    bio.name = 'prediction.png'
    img.save(bio, 'PNG')
    bio.seek(0)

    await update.message.reply_photo(photo=bio)

    # Ready for next signal
    buttons = [[InlineKeyboardButton("🔄 Ready for Next Signal", callback_data="next_signal")]]
    await update.message.reply_text("✅ Signal sent!", reply_markup=InlineKeyboardMarkup(buttons))
    return ConversationHandler.END

# --- Next Signal Button ---
async def handle_next_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("✍️ Please enter your next *Client Seed*:", parse_mode="Markdown")
    return ENTER_CLIENT_SEED

# --- Bot Setup ---
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECT_PLAN: [CallbackQueryHandler(plan_selected)],
            ENTER_PASSKEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_passkey)],
            ENTER_CLIENT_SEED: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_client_seed),
                CallbackQueryHandler(handle_next_signal, pattern="^next_signal$")
            ]
        },
        fallbacks=[],
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
