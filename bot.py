import os
import logging
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# --------- LOGGING ---------
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# --------- ENV ---------
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
API = os.environ.get("API_URL")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

CARD = "6221061258771031"

shop_open = True

prices = {
    "1 گیگ": 450,
    "2 گیگ": 820,
    "3 گیگ": 1150,
    "4 گیگ": 1450,
    "5 گیگ": 1750,
    "10 گیگ": 3200,
    "20 گیگ": 5800
}

user_plan = {}

# --------- KEYBOARD ---------
def main_kb():
    return ReplyKeyboardMarkup(
        [["🌐 سایت", "📞 پشتیبانی"]],
        resize_keyboard=True
    )

# --------- START ---------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("START command received")

    uid = update.effective_user.id

    if context.args:
        plan = " ".join(context.args)
        user_plan[uid] = plan

        if not shop_open:
            await update.message.reply_text("🔴 فروش بسته است")
            return

        try:
            stock = requests.get(f"{API}/stock").json()
        except:
            await update.message.reply_text("❌ خطا در اتصال به سرور")
            return

        if stock.get(plan, 0) == 0:
            await update.message.reply_text("❌ موجودی این پلن تموم شده")
            return

        price = prices.get(plan, "نامشخص")

        await update.message.reply_text(
            f"📦 {plan}\n"
            f"💰 {price} هزار تومان\n\n"
            f"💳 `{CARD}`\n\n"
            f"📸 رسید رو بفرست",
            parse_mode="Markdown"
        )

    else:
        await update.message.reply_text(
            "سلام 👋\nاز سایت اقدام کن 👇\nhttps://ttrustsales.lovable.app/",
            reply_markup=main_kb()
        )

# --------- PHOTO ---------
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if uid not in user_plan:
        await update.message.reply_text("❌ اول از سایت اقدام کن")
        return

    plan = user_plan[uid]

    if not shop_open:
        await update.message.reply_text("🔴 فروش بسته است")
        return

    try:
        stock = requests.get(f"{API}/stock").json()
    except:
        await update.message.reply_text("❌ خطا در اتصال به سرور")
        return

    if stock.get(plan, 0) == 0:
        await update.message.reply_text("❌ موجودی تموم شده")
        return

    try:
        res = requests.post(f"{API}/buy", json={"plan": plan}).json()
    except:
        await update.message.reply_text("❌ خطا در خرید")
        return

    if res.get("status") != "ok":
        await update.message.reply_text("❌ موجودی تموم شد")
        return

    config = res.get("config")

    await update.message.reply_text(
        f"✅ خرید تایید شد\n\n📦 {plan}\n\n`{config}`",
        parse_mode="Markdown"
    )

    # ارسال به ادمین
    if ADMIN_ID:
        await context.bot.send_message(
            ADMIN_ID,
            f"📥 فروش جدید\n👤 {uid}\n📦 {plan}"
        )

    del user_plan[uid]

# --------- TEXT ---------
async def text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t = update.message.text

    if t == "🌐 سایت":
        await update.message.reply_text("https://ttrustsales.lovable.app/")
    elif t == "📞 پشتیبانی":
        await update.message.reply_text("@your_support_id")

# --------- ADMIN ---------
async def open_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global shop_open
    if update.effective_user.id == ADMIN_ID:
        shop_open = True
        await update.message.reply_text("🟢 فروش باز شد")

async def close_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global shop_open
    if update.effective_user.id == ADMIN_ID:
        shop_open = False
        await update.message.reply_text("🔴 فروش بسته شد")

# --------- MAIN ---------
def main():
    if not TOKEN:
        print("❌ TOKEN تنظیم نشده")
        return

    print("🤖 Bot is running...")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("open", open_shop))
    app.add_handler(CommandHandler("close", close_shop))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text))

    app.run_polling()

if __name__ == "__main__":
    main()
