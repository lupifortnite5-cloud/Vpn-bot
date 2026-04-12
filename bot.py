import os
import json
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

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

# ------------------ فایل‌ها ------------------

def load_configs():
    try:
        with open("configs.json", "r") as f:
            return json.load(f)
    except:
        return {plan: [] for plan in plans}

def save_configs():
    with open("configs.json", "w") as f:
        json.dump(configs, f)

def load_sales():
    try:
        with open("sales.json", "r") as f:
            return json.load(f)
    except:
        return []

def save_sales():
    with open("sales.json", "w") as f:
        json.dump(sales, f)

configs = load_configs()
sales = load_sales()

user_plans = {}
pending_orders = {}

# ------------------ کیبورد ------------------

def main_keyboard():
    return ReplyKeyboardMarkup(
        [["خرید VPN"], ["پلن‌ها"], ["پشتیبانی"]],
        resize_keyboard=True
    )

# ------------------ دستورات ------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام 👋", reply_markup=main_keyboard())

async def open_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global shop_open
    if update.message.from_user.id == ADMIN_ID:
        shop_open = True
        await update.message.reply_text("✅ فروش باز شد")

async def close_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global shop_open
    if update.message.from_user.id == ADMIN_ID:
        shop_open = False
        await update.message.reply_text("🔴 فروش بسته شد")

# ➕ اضافه کردن کانفیگ
async def add_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    try:
        parts = update.message.text.split(" ", 1)
        data = parts[1]
        plan, config = data.split("|", 1)

        plan = plan.strip()
        config = config.strip()

        configs[plan].append(config)
        save_configs()

        await update.message.reply_text(f"✅ اضافه شد\n📦 {len(configs[plan])}")
    except:
        await update.message.reply_text("❌ فرمت اشتباه")

# 📦 موجودی
async def stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    msg = "📦 موجودی:\n\n"
    for p, lst in configs.items():
        msg += f"{p}: {len(lst)} عدد\n"

    await update.message.reply_text(msg)

# 📊 فروش‌ها
async def sales_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    if not sales:
        await update.message.reply_text("❌ فروشی ثبت نشده")
        return

    msg = "📊 فروش‌ها:\n\n"
    for s in sales[-10:]:
        msg += f"👤 {s['user']} | {s['plan']}\n"

    await update.message.reply_text(msg)

# ------------------ پیام‌ها ------------------

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global shop_open
    text = update.message.text
    user = update.message.from_user

    # تایید ادمین
    if user.id == ADMIN_ID and update.message.reply_to_message:
        replied_id = update.message.reply_to_message.message_id
        customer_id = pending_orders.get(replied_id)

        if customer_id:
            plan = user_plans.get(customer_id)

            if not plan or len(configs[plan]) == 0:
                await update.message.reply_text("❌ موجودی نداریم")
                return

            config = configs[plan].pop(0)
            save_configs()

            # ذخیره فروش
            sales.append({
                "user": customer_id,
                "plan": plan,
                "config": config
            })
            save_sales()

            await context.bot.send_message(
                chat_id=customer_id,
                text=f"✅ کانفیگ شما:\n\n{config}"
            )

            await update.message.reply_text("✅ ارسال شد")
            del pending_orders[replied_id]
        return

    if text == "خرید VPN":
        if not shop_open:
            await update.message.reply_text("🔴 فروش بسته است")
            return

        keyboard = [[p] for p in plans]
        await update.message.reply_text(
            "پلن رو انتخاب کن:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )

    elif text in plans:
        if not shop_open:
            await update.message.reply_text("🔴 فروش بسته است")
            return

        if len(configs[text]) == 0:
            await update.message.reply_text("❌ موجود نیست")
            return

        user_plans[user.id] = text
        price = plans[text]

        await update.message.reply_text(
            f"📦 {text}\n💰 {price}\n\n💳 {CARD_NUMBER}\n👤 {CARD_OWNER}\n\n📸 رسید بفرست"
        )

    elif text == "پلن‌ها":
        msg = "📦 پلن‌ها:\n\n"
        for p, price in plans.items():
            msg += f"{p}: {price}\n"
        await update.message.reply_text(msg)

    elif text == "پشتیبانی":
        await update.message.reply_text("📞 @TtrustVPN_support")

    else:
        await update.message.reply_text("از منو استفاده کن", reply_markup=main_keyboard())

# ------------------ رسید ------------------

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    plan = user_plans.get(user.id)

    if not plan:
        return

    await context.bot.forward_message(
        chat_id=ADMIN_ID,
        from_chat_id=user.id,
        message_id=update.message.message_id
    )

    info_msg = await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📥 رسید\n👤 {user.first_name}\n🆔 {user.id}\n📦 {plan}\n\nریپلای کن"
    )

    pending_orders[info_msg.message_id] = user.id

    await update.message.reply_text("✅ ارسال شد، منتظر تایید")

# ------------------ اجرا ------------------

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("open", open_shop))
    app.add_handler(CommandHandler("close", close_shop))
    app.add_handler(CommandHandler("add", add_config))
    app.add_handler(CommandHandler("stock", stock))
    app.add_handler(CommandHandler("sales", sales_report))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_media))

    app.run_polling()
