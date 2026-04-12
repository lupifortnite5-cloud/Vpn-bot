import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

CARD_NUMBER = "6221061258771031"
CARD_OWNER = "ایروانی"

plans = {
    "1 گیگ - یک ماهه": "400 تومان",
    "2 گیگ - یک ماهه": "800 تومان",
    "3 گیگ - یک ماهه": "1200 تومان",
    "4 گیگ - یک ماهه": "1600 تومان",
    "5 گیگ - یک ماهه": "2000 تومان",
    "6 گیگ - یک ماهه": "2400 تومان",
    "7 گیگ - یک ماهه": "2800 تومان",
    "8 گیگ - یک ماهه": "3200 تومان",
    "9 گیگ - یک ماهه": "3600 تومان",
    "10 گیگ - یک ماهه": "4000 تومان",
}

# 📦 موجودی
configs = {plan: [] for plan in plans}

user_plans = {}

def main_keyboard():
    return ReplyKeyboardMarkup([["خرید VPN"], ["پلن‌ها"], ["پشتیبانی"]], resize_keyboard=True)

# 🚀 شروع
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام 👋\nبه ربات فروش VPN خوش اومدی", reply_markup=main_keyboard())

# ➕ اضافه کردن کانفیگ (اصلاح شده)
async def add_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    try:
        # جدا کردن دستور از متن
        parts = update.message.text.split(" ", 1)
        if len(parts) < 2:
            raise Exception("no data")

        data = parts[1]

        # جدا کردن پلن و کانفیگ
        if "|" not in data:
            raise Exception("format error")

        plan, config = data.split("|", 1)

        plan = plan.strip()
        config = config.strip()

        if plan not in configs:
            await update.message.reply_text("❌ اسم پلن اشتباهه")
            return

        configs[plan].append(config)

        await update.message.reply_text(
            f"✅ کانفیگ اضافه شد\n\n📦 پلن: {plan}\n📊 موجودی: {len(configs[plan])}"
        )

    except:
        await update.message.reply_text(
            "❌ فرمت اشتباه\n\n"
            "📌 مثال درست:\n"
            "/add 1 گیگ - یک ماهه | vless://xxxx"
        )

# 📦 نمایش موجودی
async def stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    msg = "📦 موجودی:\n\n"
    for plan, lst in configs.items():
        msg += f"{plan}: {len(lst)} عدد\n"

    await update.message.reply_text(msg)

# 🛒 خرید
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.message.from_user

    if text == "خرید VPN":
        keyboard = [[plan] for plan in plans.keys()]
        await update.message.reply_text(
            "یکی از پلن‌ها رو انتخاب کن:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )

    elif text in plans:
        # ❌ اگر موجودی نیست
        if len(configs[text]) == 0:
            await update.message.reply_text("❌ این پلن فعلاً موجود نیست")
            return

        user_plans[user.id] = text

        await update.message.reply_text(
            f"💰 پرداخت به:\n{CARD_NUMBER}\n{CARD_OWNER}\n\nرسید رو بفرست"
        )

    elif text == "پلن‌ها":
        msg = "📦 پلن‌ها:\n\n"
        for p, price in plans.items():
            msg += f"{p}: {price}\n"
        await update.message.reply_text(msg)

    elif text == "پشتیبانی":
        await update.message.reply_text("📞 @TtrustVPN_support")

    else:
        await update.message.reply_text("از منو استفاده کن 👇", reply_markup=main_keyboard())

# 📥 دریافت رسید و ارسال کانفیگ
async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    plan = user_plans.get(user.id)

    if not plan:
        await update.message.reply_text("❌ اول پلن انتخاب کن")
        return

    if len(configs[plan]) == 0:
        await update.message.reply_text("❌ موجودی این پلن تموم شده")
        return

    # برداشتن کانفیگ (حذف از لیست)
    config = configs[plan].pop(0)

    await context.bot.send_message(
        chat_id=user.id,
        text=f"✅ کانفیگ شما:\n\n{config}"
    )

    await update.message.reply_text("✅ ارسال شد")

# ▶️ اجرا
if __name__ == "__main__":
    if not TOKEN:
        raise RuntimeError("TOKEN تنظیم نشده")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_config))
    app.add_handler(CommandHandler("stock", stock))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_media))

    print("Bot running...")
    app.run_polling()
