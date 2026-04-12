import os
import json
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

CARD_NUMBER = "6221061258771031"
CARD_OWNER = "ایروانی"

shop_open = True

plans = {
    "1 گیگ - یک ماهه": "400 تومان",
    "2 گیگ - یک ماهه": "800 تومان",
    "3 گیگ - یک ماهه": "1200 تومان",
    "4 گیگ - یک ماهه": "1600 تومان",
    "5 گیگ - یک ماهه": "2000 تومان",
}

plan_list = list(plans.keys())

# ---------- DATA ----------
def load_json(name, default):
    try:
        with open(name, "r") as f:
            return json.load(f)
    except:
        return default


def save_json(name, data):
    with open(name, "w") as f:
        json.dump(data, f)


configs = load_json("configs.json", {p: [] for p in plans})
sales = load_json("sales.json", [])
users = load_json("users.json", {})

cart = {}
user_plans = {}
pending_orders = {}

# ---------- KEYBOARDS ----------
def main_keyboard(user_id):
    kb = [["🛒 خرید VPN"], ["📦 پلن‌ها"]]

    if user_id == ADMIN_ID:
        kb.append(["🛠 پنل ادمین"])

    return ReplyKeyboardMarkup(kb, resize_keyboard=True)


def admin_panel():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📦 استاک", callback_data="stock")],
        [InlineKeyboardButton("➕ اضافه کانفیگ", callback_data="add")],
        [InlineKeyboardButton("🗑 حذف کانفیگ", callback_data="remove")],
        [InlineKeyboardButton("📊 آمار", callback_data="stats")],
        [InlineKeyboardButton("💾 بکاپ", callback_data="backup")],
    ])


# ---------- START ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    users[str(uid)] = users.get(str(uid), 0) + 1
    save_json("users.json", users)

    await update.message.reply_text(
        "سلام 👋 خوش اومدی",
        reply_markup=main_keyboard(uid),
    )


# ---------- TEXT ----------
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global shop_open

    text = update.message.text
    user = update.message.from_user
    uid = user.id

    # admin panel
    if text == "🛠 پنل ادمین" and uid == ADMIN_ID:
        await update.message.reply_text("پنل ادمین:", reply_markup=admin_panel())
        return

    # buy menu
    if text == "🛒 خرید VPN":
        if not shop_open:
            await update.message.reply_text("🔴 فروش بسته است")
            return

        kb = [[p] for p in plans]
        await update.message.reply_text(
            "پلن رو انتخاب کن:",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        )
        return

    # add to cart
    if text in plans:
        cart.setdefault(uid, [])
        cart[uid].append(text)

        await update.message.reply_text(
            f"➕ اضافه شد به سبد:\n{text}\n\n🛒 برای نهایی کردن رسید بفرست"
        )
        return

    # show plans
    if text == "📦 پلن‌ها":
        msg = "📦 پلن‌ها:\n\n"
        for p, price in plans.items():
            msg += f"{p} : {price}\n"
        await update.message.reply_text(msg)
        return

    await update.message.reply_text("از منو استفاده کن", reply_markup=main_keyboard(uid))


# ---------- RECEIPT ----------
async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    uid = user.id

    if uid not in cart or not cart[uid]:
        return

    await context.bot.forward_message(
        ADMIN_ID,
        uid,
        update.message.message_id
    )

    msg = await context.bot.send_message(
        ADMIN_ID,
        f"📥 سفارش جدید\n👤 {user.first_name}\n🆔 {uid}\n\nریپلای کن برای تایید"
    )

    pending_orders[msg.message_id] = uid

    await update.message.reply_text("✅ رسید دریافت شد")


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

    if uid not in cart or not cart[uid]:
        await update.message.reply_text("❌ سبد خالیه")
        return

    plan = cart[uid].pop(0)

    if len(configs[plan]) == 0:
        await update.message.reply_text("❌ موجودی نداریم")
        return

    config = configs[plan].pop(0)

    save_json("configs.json", configs)

    sales.append({
        "user": uid,
        "plan": plan,
        "config": config,
    })
    save_json("sales.json", sales)

    await context.bot.send_message(
        uid,
        f"✅ کانفیگ شما:\n\n`{config}`",
        parse_mode="Markdown",
    )

    await update.message.reply_text("✅ ارسال شد")


# ---------- CALLBACK ADMIN ----------
async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.from_user.id != ADMIN_ID:
        return

    data = q.data

    if data == "stock":
        msg = "📦 استاک:\n\n"
        for p, lst in configs.items():
            msg += f"{p} ({len(lst)})\n"
        await q.message.reply_text(msg)

    elif data == "stats":
        await q.message.reply_text(
            f"👤 کاربران: {len(users)}\n📊 فروش: {len(sales)}"
        )

    elif data == "backup":
        await context.bot.send_document(ADMIN_ID, open("configs.json", "rb"))
        await context.bot.send_document(ADMIN_ID, open("sales.json", "rb"))
        await q.message.reply_text("✅ بکاپ")

    elif data == "remove":
        await q.message.reply_text("برای حذف: /remove index")

    elif data == "add":
        await q.message.reply_text("برای اضافه: /add1 ... /add5")


# ---------- STOCK ----------
async def stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    msg = "📦 استاک کامل:\n\n"
    for p, lst in configs.items():
        msg += f"{p}:\n"
        for i, c in enumerate(lst, 1):
            msg += f"{i}. {c}\n"
        msg += "\n"

    await update.message.reply_text(msg)


# ---------- REMOVE ----------
async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    try:
        i = int(context.args[0]) - 1
        p = plan_list[int(context.args[1]) - 1]

        removed = configs[p].pop(i)
        save_json("configs.json", configs)

        await update.message.reply_text(f"🗑 حذف شد:\n{removed}")

    except:
        await update.message.reply_text("❌ /remove index plan")


# ---------- APP ----------
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("remove", remove))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_media))

app.add_handler(CallbackQueryHandler(callback))

app.run_polling()
