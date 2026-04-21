import os, requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
API = os.environ.get("API_URL")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))

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

# ---------- KEYBOARD ----------
def main_kb():
    return ReplyKeyboardMarkup(
        [["🌐 سایت"], ["📞 پشتیبانی"]],
        resize_keyboard=True
    )

# ---------- START ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if context.args:
        plan = " ".join(context.args)
        user_plan[uid] = plan

        if not shop_open:
            await update.message.reply_text("🔴 فروش بسته است")
            return

        stock = requests.get(f"{API}/stock").json()

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
            "از سایت اقدام کن 👇\nhttps://ttrustsales.lovable.app/",
            reply_markup=main_kb()
        )

# ---------- RECEIPT ----------
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if uid not in user_plan:
        await update.message.reply_text("❌ از سایت وارد شو")
        return

    plan = user_plan[uid]

    if not shop_open:
        await update.message.reply_text("🔴 فروش بسته است")
        return

    stock = requests.get(f"{API}/stock").json()

    if stock.get(plan, 0) == 0:
        await update.message.reply_text("❌ موجودی تموم شده")
        return

    res = requests.post(f"{API}/buy", json={"plan": plan}).json()

    if res["status"] == "no_stock":
        await update.message.reply_text("❌ موجودی تموم شد")
        return

    config = res["config"]

    await update.message.reply_text(
        f"✅ خرید تایید شد\n\n📦 {plan}\n\n`{config}`",
        parse_mode="Markdown"
    )

    # ارسال به ادمین
    await context.bot.send_message(
        ADMIN_ID,
        f"📥 فروش جدید\n\n👤 ID: {uid}\n📦 {plan}"
    )

    del user_plan[uid]

# ---------- ADMIN ----------
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

# ---------- MAIN ----------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("open", open_shop))
    app.add_handler(CommandHandler("close", close_shop))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    app.run_polling()

if __name__ == "__main__":
    main()
