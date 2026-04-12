import os
import json
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

SUPPORT_ID = "@your_support_id"  # 👈 پشتیبانی

CARD_NUMBER = "6221061258771031"
CARD_OWNER = "ایروانی"

shop_open = True

plans = {
    "1 گیگ - یک ماهه": 400,
    "2 گیگ - یک ماهه": 800,
    "3 گیگ - یک ماهه": 1200,
    "4 گیگ - یک ماهه": 1600,
    "5 گیگ - یک ماهه": 2000,
}

plan_list = list(plans.keys())

# ---------- DATA ----------
def load(name, default):
    try:
        with open(name, "r") as f:
            return json.load(f)
    except:
        return default

def save(name, data):
    with open(name, "w") as f:
        json.dump(data, f)

configs = load("configs.json", {p: [] for p in plans})
sales = load("sales.json", [])
users = load("users.json", {})

cart = {}
pending_orders = {}

# ---------- KEYBOARD ----------
def main_keyboard(uid):
    kb = [["🛒 خرید VPN"], ["📦 پلن‌ها"], ["📞 پشتیبانی"]]

    if uid == ADMIN_ID:
        kb.append(["🛠 پنل ادمین"])

    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

# ---------- START ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    users[str(uid)] = users.get(str(uid), 0) + 1
    save("users.json", users)

    await update.message.reply_text("سلام 👋", reply_markup=main_keyboard(uid))

# ---------- TEXT ----------
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.message.from_user
    uid = user.id

    # support
    if text == "📞 پشتیبانی":
        await update.message.reply_text(f"📞 پشتیبانی:\n{SUPPORT_ID}")
        return

    # admin panel
    if text == "🛠 پنل ادمین" and uid == ADMIN_ID:
        await update.message.reply_text("پنل ادمین فعال است")
        return

    # buy
    if text == "🛒 خرید VPN":
        kb = [[p] for p in plans]
        await update.message.reply_text(
            "پلن رو انتخاب کن:",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
        )
        return

    # add to cart (with quantity support)
    if text in plans:
        cart.setdefault(uid, {})

        cart[uid][text] = cart[uid].get(text, 0) + 1

        await update.message.reply_text(
            f"➕ اضافه شد:\n{text}\n"
            f"📦 تعداد: {cart[uid][text]}"
        )
        return

    # plans list
    if text == "📦 پلن‌ها":
        msg = "📦 پلن‌ها:\n\n"
        for p, price in plans.items():
            msg += f"{p}: {price} تومان\n"
        await update.message.reply_text(msg)
        return

    await update.message.reply_text("از منو استفاده کن", reply_markup=main_keyboard(uid))

# ---------- RECEIPT ----------
async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    uid = user.id

    if uid not in cart:
        return

    total = 0
    summary = ""

    for plan, count in cart[uid].items():
        price = plans[plan]
        total += price * count
        summary += f"{plan} × {count}\n"

    msg = await context.bot.send_message(
        ADMIN_ID,
        f"📥 سفارش جدید\n👤 {user.first_name}\n🆔 {uid}\n\n{summary}\n💰 جمع کل: {total} تومان\n\nریپلای کن"
    )

    pending_orders[msg.message_id] = uid

    await update.message.reply_text("✅ سفارش ثبت شد")

# ---------- ADMIN REPLY ----------
async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    if not update.message.reply_to_message:
        return

    mid = update.message.reply_to_message.message_id
    uid = pending_orders.get(mid)

    if not uid:
        return

    cart[uid] = {}

    await context.bot.send_message(
        uid,
        "✅ سفارش شما تایید شد و در حال آماده‌سازی است"
    )

    await update.message.reply_text("ارسال شد")

# ---------- RUN ----------
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_media))

app.run_polling()
