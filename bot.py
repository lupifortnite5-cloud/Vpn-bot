import os
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
    "6 گیگ - یک ماهه": "2400 تومان",
    "7 گیگ - یک ماهه": "2800 تومان",
    "8 گیگ - یک ماهه": "3200 تومان",
    "9 گیگ - یک ماهه": "3600 تومان",
    "10 گیگ - یک ماهه": "4000 تومان",
}

user_plans = {}
pending_orders = {}

def main_keyboard():
    keyboard = [["خرید VPN"], ["پلن‌ها"], ["پشتیبانی"]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام 👋\nبه ربات فروش VPN خوش اومدی",
        reply_markup=main_keyboard()
    )

async def open_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global shop_open
    if update.message.from_user.id != ADMIN_ID:
        return
    shop_open = True
    await update.message.reply_text("✅ فروش باز شد.")

async def close_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global shop_open
    if update.message.from_user.id != ADMIN_ID:
        return
    shop_open = False
    await update.message.reply_text("🔴 فروش بسته شد.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global shop_open
    text = update.message.text
    user = update.message.from_user

    if user.id == ADMIN_ID and update.message.reply_to_message:
        replied_id = update.message.reply_to_message.message_id
        customer_id = pending_orders.get(replied_id)
        if customer_id:
            await context.bot.send_message(
                chat_id=customer_id,
                text=f"✅ کانفیگ VPN شما آماده‌ست:\n\n{text}"
            )
            await update.message.reply_text("✅ کانفیگ برای مشتری ارسال شد.")
            del pending_orders[replied_id]
        return

    if text == "خرید VPN":
        if not shop_open:
            await update.message.reply_text(
                "🔴 فروش در حال حاضر بسته است.\nبعداً مراجعه کنید.",
                reply_markup=main_keyboard()
            )
            return
        keyboard = [[plan] for plan in plans.keys()]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("یکی از پلن‌ها رو انتخاب کن:", reply_markup=reply_markup)

    elif text in plans:
        if not shop_open:
            await update.message.reply_text("🔴 فروش در حال حاضر بسته است.", reply_markup=main_keyboard())
            return
        plan_price = plans[text]
        user_plans[user.id] = text
        await update.message.reply_text(
            f"✅ پلن انتخابی: {text}\n"
            f"💰 قیمت: {plan_price}\n\n"
            f"💳 کارت به کارت کن به:\n"
            f"`{CARD_NUMBER}`\n"
            f"به نام: {CARD_OWNER}\n\n"
            f"بعد از پرداخت، عکس رسید رو بفرست.",
            parse_mode="Markdown",
            reply_markup=main_keyboard()
        )

    elif text == "پلن‌ها":
        msg = "📦 لیست پلن‌ها:\n\n"
        for p, price in plans.items():
            msg += f"• {p}: {price}\n"
        await update.message.reply_text(msg)

    elif text == "پشتیبانی":
        await update.message.reply_text("📞 پشتیبانی:\n\n@TtrustVPN_support")

    else:
        await update.message.reply_text("از دکمه‌های منو استفاده کن 👇", reply_markup=main_keyboard())

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user

    if user.id == ADMIN_ID and update.message.reply_to_message:
        replied_id = update.message.reply_to_message.message_id
        customer_id = pending_orders.get(replied_id)
        if customer_id:
            await context.bot.copy_message(
                chat_id=customer_id,
                from_chat_id=ADMIN_ID,
                message_id=update.message.message_id,
                caption="✅ کانفیگ VPN شما آماده‌ست!"
            )
            await update.message.reply_text("✅ کانفیگ برای مشتری ارسال شد.")
            del pending_orders[replied_id]
        return

    plan = user_plans.get(user.id, "نامشخص")
    username = f"@{user.username}" if user.username else "ندارد"

    await context.bot.forward_message(chat_id=ADMIN_ID, from_chat_id=user.id, message_id=update.message.message_id)

    info_msg = await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            f"📥 رسید پرداخت جدید:\n\n"
            f"👤 نام: {user.first_name}\n"
            f"🆔 یوزرنیم: {username}\n"
            f"🔢 آیدی: {user.id}\n"
            f"📦 پلن: {plan}\n\n"
            f"⬆️ برای ارسال کانفیگ، به این پیام ریپلای کن."
        )
    )

    pending_orders[info_msg.message_id] = user.id
    await update.message.reply_text("✅ رسید دریافت شد!\nبعد از تایید توسط ادمین، کانفیگ برات ارسال میشه. ⏳")

if __name__ == "__main__":
    if not TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("open", open_shop))
    app.add_handler(CommandHandler("close", close_shop))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_media))
    print("Bot is running...")
    app.run_polling()
