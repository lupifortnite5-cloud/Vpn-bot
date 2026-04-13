import json
import logging
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters,
)

# 🔴 اینا رو خودت پر کن
TOKEN = "PUT_YOUR_TOKEN"
ADMIN_ID = 123456789

CARD_NUMBER = "6221061258771031"
CARD_OWNER = "ایروانی"
SUPPORT_ID = "@your_support"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

plans = {
    "1 گیگ - یک ماهه": 400,
    "2 گیگ - یک ماهه": 800,
    "3 گیگ - یک ماهه": 1200,
    "4 گیگ - یک ماهه": 1600,
    "5 گیگ - یک ماهه": 2000,
}

# ---------- دیتابیس ----------

def load_data():
    try:
        with open("data.json", "r") as f:
            return json.load(f)
    except:
        return {"configs": {p: [] for p in plans}, "sales": []}

def save_data():
    with open("data.json", "w") as f:
        json.dump(data, f)

data = load_data()
configs = data["configs"]
sales = data["sales"]

pending_orders = {}
shop_open = True

# ---------- کیبورد ----------

def main_keyboard(uid):
    kb = [
        ["🛒 خرید VPN"],
        ["📦 پلن‌ها"],
        ["📞 پشتیبانی"],
    ]
    if uid == ADMIN_ID:
        kb.append(["🛠 پنل ادمین"])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

def admin_panel():
    btn = "🔴 بستن فروش" if shop_open else "🟢 باز کردن فروش"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📦 استاک", callback_data="stock")],
        [InlineKeyboardButton("📊 فروش", callback_data="sales")],
        [InlineKeyboardButton("💾 بکاپ", callback_data="backup")],
        [InlineKeyboardButton(btn, callback_data="toggle")],
    ])

# ---------- start ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام 👋",
        reply_markup=main_keyboard(update.effective_user.id)
    )

# ---------- باز و بسته ----------

async def open_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global shop_open
    if update.effective_user.id != ADMIN_ID:
        return
    shop_open = True
    await update.message.reply_text("🟢 فروش باز شد")

async def close_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global shop_open
    if update.effective_user.id != ADMIN_ID:
        return
    shop_open = False
    await update.message.reply_text("🔴 فروش بسته شد")

# ---------- اضافه کردن ----------

async def add_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        cmd = update.message.text.split()[0]
        config = update.message.text.replace(cmd, "").strip()

        mapping = {
            "/add1": list(plans.keys())[0],
            "/add2": list(plans.keys())[1],
            "/add3": list(plans.keys())[2],
            "/add4": list(plans.keys())[3],
            "/add5": list(plans.keys())[4],
        }

        plan = mapping.get(cmd)

        if not plan or not config:
            await update.message.reply_text("❌ فرمت اشتباه")
            return

        configs[plan].append(config)
        save_data()

        await update.message.reply_text(f"✅ اضافه شد\n📦 {len(configs[plan])}")

    except:
        await update.message.reply_text("❌ خطا")

# ---------- متن ----------

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global shop_open

    text = update.message.text
    user = update.effective_user
    uid = user.id

    if text == "📞 پشتیبانی":
        await update.message.reply_text(SUPPORT_ID)
        return

    if text == "📦 پلن‌ها":
        msg = "📦 پلن‌ها:\n\n"
        for p, price in plans.items():
            msg += f"{p}: {price} تومان\n"
        await update.message.reply_text(msg)
        return

    if text == "🛒 خرید VPN":
        if not shop_open:
            await update.message.reply_text("🔴 فروش بسته است")
            return

        kb = [[p] for p in plans]
        await update.message.reply_text(
            "پلن رو انتخاب کن:",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
        )
        return

    if text in plans:
        if len(configs[text]) == 0:
            await update.message.reply_text("❌ موجود نیست")
            return

        price = plans[text]

        await update.message.reply_text(
            f"📦 {text}\n"
            f"💰 {price} تومان\n\n"
            f"💳 شماره کارت:\n`{CARD_NUMBER}`\n"
            f"👤 {CARD_OWNER}\n\n"
            f"📸 رسید رو ارسال کن",
            parse_mode="Markdown"
        )

        pending_orders[uid] = text
        return

    if text == "🛠 پنل ادمین" and uid == ADMIN_ID:
        status = "🟢 باز" if shop_open else "🔴 بسته"
        await update.message.reply_text(f"پنل ادمین\nوضعیت: {status}", reply_markup=admin_panel())
        return

# ---------- عکس ----------

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = user.id

    if uid not in pending_orders:
        return

    plan = pending_orders[uid]

    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ تایید", callback_data=f"ok|{uid}"),
            InlineKeyboardButton("❌ رد", callback_data=f"no|{uid}")
        ]
    ])

    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=update.message.photo[-1].file_id,
        caption=f"📥 رسید\n👤 {uid}\n📦 {plan}",
        reply_markup=kb
    )

    await update.message.reply_text("✅ رسید ارسال شد، منتظر تایید")

# ---------- دکمه ----------

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global shop_open

    q = update.callback_query
    await q.answer()
    data_cb = q.data

    if data_cb == "stock":
        msg = ""
        for p, lst in configs.items():
            msg += f"{p}: {len(lst)}\n"
        await q.message.edit_text(msg)

    elif data_cb == "sales":
        msg = f"تعداد فروش: {len(sales)}"
        await q.message.edit_text(msg)

    elif data_cb == "backup":
        with open("data.json", "rb") as f:
            await context.bot.send_document(ADMIN_ID, f)
        await q.message.edit_text("ارسال شد")

    elif data_cb == "toggle":
        shop_open = not shop_open
        status = "🟢 فروش باز شد" if shop_open else "🔴 فروش بسته شد"
        await q.message.edit_text(status, reply_markup=admin_panel())

    elif data_cb.startswith("ok|"):
        uid = int(data_cb.split("|")[1])
        plan = pending_orders.get(uid)

        if not plan or len(configs[plan]) == 0:
            await q.message.edit_caption("❌ موجودی نیست")
            return

        config = configs[plan].pop(0)
        save_data()

        sales.append({"user": uid, "plan": plan, "config": config})
        save_data()

        await context.bot.send_message(
            uid,
            f"✅ کانفیگ شما:\n\n`{config}`",
            parse_mode="Markdown"
        )

        await q.message.edit_caption("✅ ارسال شد")
        del pending_orders[uid]

    elif data_cb.startswith("no|"):
        uid = int(data_cb.split("|")[1])
        await context.bot.send_message(uid, "❌ رد شد")
        del pending_orders[uid]
        await q.message.edit_caption("رد شد")

# ---------- اجرا ----------

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("open", open_shop))
    app.add_handler(CommandHandler("close", close_shop))

    app.add_handler(CommandHandler("add1", add_config))
    app.add_handler(CommandHandler("add2", add_config))
    app.add_handler(CommandHandler("add3", add_config))
    app.add_handler(CommandHandler("add4", add_config))
    app.add_handler(CommandHandler("add5", add_config))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CallbackQueryHandler(handle_callback))

    print("Bot Running...")
    app.run_polling()

if __name__ == "__main__":
    main()
